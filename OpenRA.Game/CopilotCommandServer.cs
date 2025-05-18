using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace OpenRA
{
	public class CopilotCommandServer
	{
		readonly Socket serverSocket = new(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
		readonly int port;
		readonly World world;
		bool isRunning;
		private const string CurrentApiVersion = "1.0";

		public delegate string CommandHandler(JObject json, World world);
		public delegate JObject QueryHandler(JObject json, World world);

		public Dictionary<string, CommandHandler> CommandHandlers = new();
		public Dictionary<string, QueryHandler> QueryHandlers = new();

		public CopilotCommandServer(int port, World world)
		{
			this.port = port;
			this.world = world;
		}

		~CopilotCommandServer()
		{
			End();
		}

		public void Start()
		{
			serverSocket.Bind(new IPEndPoint(IPAddress.Any, port));
			serverSocket.Listen(10);
			isRunning = true;
			Console.WriteLine($"Listening for connections on port {port}");

			Task.Run(async () =>
			{
				while (isRunning)
				{
					try
					{
						var clientSocket = await serverSocket.AcceptAsync();
						HandleClient(clientSocket);
					}
					catch (SocketException) when (!isRunning)
					{
						break;
					}
				}
			});
		}

		public void End()
		{
			if (isRunning)
			{
				isRunning = false;
				serverSocket.Close();
				Console.WriteLine("CopilotServer has been stopped.");
			}
		}

		async void HandleClient(Socket clientSocket)
		{
			using (clientSocket)
			{
				try
				{
					if (clientSocket == null)
					{
						throw new ArgumentException("clientSocket Uninit");
					}

					var buffer = new byte[16384];
					var received = await clientSocket.ReceiveAsync(buffer, SocketFlags.None);
					var jsonString = Encoding.UTF8.GetString(buffer, 0, received);
					Console.WriteLine("Received:" + jsonString);

					MCPRequest request;
					try
					{
						request = JsonConvert.DeserializeObject<MCPRequest>(jsonString);
					}
					catch (JsonException)
					{
						SendErrorResponse(clientSocket, new MCPError
						{
							Code = MCPErrorCodes.InvalidRequest,
							Message = "无效的JSON格式"
						});
						return;
					}

					// 验证请求
					var (isValid, validationError) = MCPValidator.ValidateRequest(request);
					if (!isValid)
					{
						SendErrorResponse(clientSocket, validationError);
						return;
					}

					// 验证API版本
					if (request.ApiVersion != CurrentApiVersion)
					{
						SendErrorResponse(clientSocket, new MCPError
						{
							Code = MCPErrorCodes.InvalidVersion,
							Message = $"不支持的API版本，当前版本: {CurrentApiVersion}"
						});
						return;
					}

					// 验证命令参数
					var (isParamsValid, paramsError) = MCPValidator.ValidateCommandParams(request.Command, request.Params);
					if (!isParamsValid)
					{
						SendErrorResponse(clientSocket, paramsError);
						return;
					}

					// 处理命令
					if (CommandHandlers.TryGetValue(request.Command, out var commandHandler))
					{
						try
						{
							var result = commandHandler?.Invoke(request.Params, world);
							SendSuccessResponse(clientSocket, result, request.RequestId);
						}
						catch (Exception ex)
						{
							SendErrorResponse(clientSocket, new MCPError
							{
								Code = MCPErrorCodes.CommandExecutionError,
								Message = "命令执行失败",
								Details = new JObject { ["error"] = ex.Message }
							}, request.RequestId);
						}
					}
					else if (QueryHandlers.TryGetValue(request.Command, out var queryHandler))
					{
						try
						{
							var resultJson = queryHandler?.Invoke(request.Params, world);
							SendSuccessResponse(clientSocket, null, request.RequestId, resultJson);
						}
						catch (Exception ex)
						{
							SendErrorResponse(clientSocket, new MCPError
							{
								Code = MCPErrorCodes.CommandExecutionError,
								Message = "查询执行失败",
								Details = new JObject { ["error"] = ex.Message }
							}, request.RequestId);
						}
					}
					else
					{
						SendErrorResponse(clientSocket, new MCPError
						{
							Code = MCPErrorCodes.InvalidCommand,
							Message = "未知的命令"
						}, request.RequestId);
					}
				}
				catch (Exception ex)
				{
					SendErrorResponse(clientSocket, new MCPError
					{
						Code = MCPErrorCodes.InternalError,
						Message = "服务器内部错误",
						Details = new JObject { ["error"] = ex.Message }
					});
				}
			}
		}

		static void SendSuccessResponse(Socket clientSocket, string message = null, string requestId = null, JObject data = null)
		{
			var response = new MCPResponse
			{
				Status = 1,
				RequestId = requestId,
				Response = message,
				Data = data
			};

			var buffer = Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(response));
			clientSocket.Send(buffer);
		}

		static void SendErrorResponse(Socket clientSocket, MCPError error, string requestId = null)
		{
			var response = new MCPResponse
			{
				Status = -1,
				RequestId = requestId,
				Error = error
			};

			var buffer = Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(response));
			clientSocket.Send(buffer);
		}

		public static string CustomJsonFormat(string json)
		{
			var stringBuilder = new StringBuilder();
			var indent = 0;
			var arrayLevel = 0;

			foreach (var ch in json)
			{
				if (ch == '[')
				{
					if (arrayLevel == 0)
					{
						stringBuilder.AppendLine(new string(' ', indent) + ch);
						indent += 2;
					}
					else
					{
						stringBuilder.Append(ch);
					}

					arrayLevel++;
				}
				else if (ch == ']')
				{
					arrayLevel--;
					if (arrayLevel == 0)
					{
						indent -= 2;
						stringBuilder.AppendLine().Append(new string(' ', indent) + ch);
					}
					else
					{
						stringBuilder.Append(ch);
					}
				}
				else if (ch == ',')
				{
					stringBuilder.Append(ch);
					if (arrayLevel == 1)
					{
						stringBuilder.AppendLine();
						stringBuilder.Append(new string(' ', indent));
					}
					else
					{
						stringBuilder.Append(' ');
					}
				}
				else
				{
					if (ch == '\n' || ch == '\r' || ch == ' ')
						continue;

					stringBuilder.Append(ch);
				}
			}

			return stringBuilder.ToString();
		}
	}
}

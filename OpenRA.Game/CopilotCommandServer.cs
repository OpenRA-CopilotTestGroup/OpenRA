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
			try
			{
				if (clientSocket == null)
				{
					throw new ArgumentException("clientSocket Uninit");
				}

				var buffer = new byte[16384];
				var received = await clientSocket.ReceiveAsync(buffer, SocketFlags.None);
				var jsonString = Encoding.UTF8.GetString(buffer, 0, received);
				Console.WriteLine("Recieved:" + jsonString);
				JObject json;
				try
				{
					json = JObject.Parse(jsonString);
				}
				catch (JsonReaderException)
				{
					SendResponse(clientSocket, "Invalid JSON format");
					return;
				}

				var command = json["command"]?.ToString();
				string result = null;
				JObject resultJson = null;

				if (CommandHandlers.TryGetValue(command, out var commandHandler))
				{
					result = commandHandler?.Invoke(json, world);
				}
				else if (QueryHandlers.TryGetValue(command, out var queryHandler))
				{
					resultJson = queryHandler?.Invoke(json, world);
				}
				else
				{
					SendResponse(clientSocket, "Unknown command");
				}

				if (resultJson != null)
				{
					SendJsonResponse(clientSocket, resultJson);
				}
				else if (result != null)
				{
					SendResponse(clientSocket, result);
				}
				else
				{
					SendResponse(clientSocket, "Command not implemented", -5);
				}
			}
			catch (Exception ex)
			{
				SendResponse(clientSocket, $"Internal Server Error: {ex.Message}", -1);
			}
			finally
			{
				clientSocket.Close();
			}
		}

		static void SendResponse(Socket clientSocket, string message, int status = 1)
		{
			// var buffer = Encoding.UTF8.GetBytes(message);
			// clientSocket.Send(buffer);
			var responseJson = new JObject
			{
				["response"] = message,
				["status"] = status
			};
			var buffer = Encoding.UTF8.GetBytes(responseJson.ToString());
			clientSocket.Send(buffer);
		}

		static void SendJsonResponse(Socket clientSocket, JObject json, int status = 1)
		{
			json["status"] = status;
			var buffer = Encoding.UTF8.GetBytes(json.ToString());
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

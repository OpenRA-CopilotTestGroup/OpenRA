using System;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace OpenRA
{
	public class CopilotCommandServer
	{
		readonly HttpListener listener = new();
		readonly string url;
		readonly World world;
		bool isRunning;

		public delegate string CommondHandler(JObject json, World world);


		//开始生产
		public event CommondHandler OnStartProdunctionCommand;

		// 移动单位指令
		public event CommondHandler OnMoveActorCommand;
		public event CommondHandler OnMoveActorOnTilePathCommand;

		// 镜头控制指令
		public event CommondHandler OnCameraMoveCommand;
		public event CommondHandler OnCameraFollowCommand;

		// 生产单位指令
		public event CommondHandler OnProduceUnitCommand;

		// 设置集结点指令
		public event CommondHandler OnSetRallyPointCommand;

		// 选择单位指令
		public event CommondHandler OnSelectUnitCommand;

		// 单位编队指令
		public event CommondHandler OnFormGroupCommand;

		public delegate JObject QueryHandler(JObject json, World world);
		public event QueryHandler QueryActor;
		public event QueryHandler QueryTile;
		public CopilotCommandServer(string url, World world)
		{
			this.url = url;
			listener.Prefixes.Add(this.url);
			this.world = world;
		}

		~CopilotCommandServer()
		{
			End();
		}

		public void Start()
		{
			listener.Start();
			isRunning = true;
			Console.WriteLine($"Listening for connections on {url}");

			Task.Run(async () =>
			{
				while (isRunning)
				{
					try
					{
						var context = await listener.GetContextAsync();
						HandleRequest(context);
					}
					catch (HttpListenerException) when (!isRunning)
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
				listener.Stop();
				listener.Close();
				Console.WriteLine("CopilotServer has been stopped.");
			}
		}

		void HandleRequest(HttpListenerContext context)
		{
			var request = context.Request;
			var response = context.Response;
			try
			{
				if (request.HttpMethod == "POST")
				{
					using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
					{
						var body = reader.ReadToEnd();

						JObject json;
						try
						{
							json = JObject.Parse(body);
						}
						catch (JsonReaderException)
						{
							SendResponse(response, "Invalid JSON format", HttpStatusCode.BadRequest);
							return;
						}
						var path = request.Url.AbsolutePath;
						string result = null;
						JObject reslut_j;
						switch (path)
						{
							case "/api/units/move":
								result = OnMoveActorCommand?.Invoke(json, world);
								break;
							case "/api/units/tilemove":
								result = OnMoveActorOnTilePathCommand?.Invoke(json, world);
								break;
							case "/api/query/actor":
								reslut_j = QueryActor?.Invoke(json, world);
								SendJsonResponse(response, reslut_j.ToString());
								return;
							case "/api/query/tile":
								reslut_j = QueryTile?.Invoke(json, world);
								SendJsonResponse(response, reslut_j.ToString());
								return;
							case "/api/produce":
								result = OnStartProdunctionCommand?.Invoke(json, world);
								break;
							case "/api/camera/move":
								result = OnCameraMoveCommand?.Invoke(json, world);
								break;
							case "/api/units/select":
								result = OnSelectUnitCommand?.Invoke(json, world);
								break;
							case "/api/units/group":
								result = OnFormGroupCommand?.Invoke(json, world);
								break;

							default:
								SendResponse(response, "Unknown command", HttpStatusCode.BadRequest);
								return;
						}

						if (result == null)
						{
							SendResponse(response, "Command not implemented", HttpStatusCode.BadRequest);
						}
						else
						{
							SendResponse(response, result);
						}
					}
				}
				else
				{
					SendResponse(response, "Invalid request", HttpStatusCode.BadRequest);
				}
			}
			catch (Exception ex)
			{
				SendResponse(response, $"Internal Server Error: {ex.Message}", HttpStatusCode.InternalServerError);
			}
		}

		static void SendResponse(HttpListenerResponse response, string message, HttpStatusCode statusCode = HttpStatusCode.OK)
		{
			var buffer = Encoding.UTF8.GetBytes(message);
			response.ContentLength64 = buffer.Length;
			response.StatusCode = (int)statusCode;
			var output = response.OutputStream;
			output.Write(buffer, 0, buffer.Length);
			output.Close();
		}
		public static string CustomJsonFormat(string json)
		{
			var stringBuilder = new StringBuilder();
			int indent = 0;
			int arrayLevel = 0;

			foreach (char ch in json)
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


		static void SendJsonResponse(HttpListenerResponse response, string json, HttpStatusCode statusCode = HttpStatusCode.OK)
		{
			var formattedJson = CustomJsonFormat(json);
			var buffer = Encoding.UTF8.GetBytes(formattedJson);
			response.ContentLength64 = buffer.Length;
			response.StatusCode = (int)statusCode;
			response.ContentType = "application/json";
			var output = response.OutputStream;
			output.Write(buffer, 0, buffer.Length);
			output.Close();
		}
	}
}

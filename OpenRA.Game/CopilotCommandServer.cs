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
		public event CommondHandler OnMoveActorCommand;
		public delegate JObject QueryHandler(JObject json, World world);
		public event QueryHandler QueryActor;
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
						var command = json["command"]?.ToString();
						string result;
						JObject reslut_j;
						switch (command)
						{
							case "moveactor":
								result = OnMoveActorCommand?.Invoke(json, world);

								SendResponse(response, result ?? "Actor moved");
								break;
							case "queryactor":
								reslut_j = QueryActor?.Invoke(json, world);
								var jsonResult = reslut_j.ToString();
								SendJsonResponse(response, jsonResult);
								break;
							default:
								SendResponse(response, "Unknown command", HttpStatusCode.BadRequest);
								break;
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
		static void SendJsonResponse(HttpListenerResponse response, string json, HttpStatusCode statusCode = HttpStatusCode.OK)
		{
			var buffer = Encoding.UTF8.GetBytes(json);
			response.ContentLength64 = buffer.Length;
			response.StatusCode = (int)statusCode;
			response.ContentType = "application/json";
			var output = response.OutputStream;
			output.Write(buffer, 0, buffer.Length);
			output.Close();
		}
	}
}

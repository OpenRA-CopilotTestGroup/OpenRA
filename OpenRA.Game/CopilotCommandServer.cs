using System;
using System.Net;
using System.Text;
using System.Threading.Tasks;

namespace OpenRA
{
	public class CopilotCommandServer
	{
		readonly HttpListener listener = new();
		readonly string url;
		readonly World world;
		bool isRunning;

		public delegate void MoveActorHandler(string args, World world);
		public event MoveActorHandler OnMoveActorCommand;
		public CopilotCommandServer(string url, World world)
		{
			this.url = url;
			listener.Prefixes.Add(this.url);
			this.world = world;
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
						// Listener was stopped, exit the loop
						break;
					}
				}
			});
		}

		public void End()
		{
			isRunning = false;
			listener.Stop();
			listener.Close();
			Console.WriteLine("CopilotServer has been stopped.");
		}

		void HandleRequest(HttpListenerContext context)
		{
			var request = context.Request;
			var response = context.Response;

			if (request.HttpMethod == "POST" && request.Url.AbsolutePath == "/moveactor")
			{
				using (var reader = new System.IO.StreamReader(request.InputStream, request.ContentEncoding))
				{
					var body = reader.ReadToEnd();
					var parameters = body.Split('&');
					var actorId = parameters[0].Split('=')[1];
					var direction = parameters[1].Split('=')[1];
					var distance = parameters[2].Split('=')[1];

					OnMoveActorCommand?.Invoke($"{actorId} {direction} {distance}", world);
				}

				const string ResponseString = "Actor moved";
				var buffer = Encoding.UTF8.GetBytes(ResponseString);
				response.ContentLength64 = buffer.Length;
				var output = response.OutputStream;
				output.Write(buffer, 0, buffer.Length);
				output.Close();
			}
			else
			{
				const string ResponseString = "Invalid request";
				var buffer = Encoding.UTF8.GetBytes(ResponseString);
				response.ContentLength64 = buffer.Length;
				var output = response.OutputStream;
				output.Write(buffer, 0, buffer.Length);
				output.Close();
			}
		}
	}
}

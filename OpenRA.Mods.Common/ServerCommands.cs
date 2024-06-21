using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Traits;
using OpenRA.Widgets;

namespace OpenRA.Mods.Common.Commands
{
	[TraitLocation(SystemActors.World)]
	[Desc("Attach this to the world actor.")]
	public class ServerCommandsInfo : TraitInfo<ServerCommands> { }
	public class ServerCommands : IWorldLoaded
	{
		World world;
		public static string MoveActorCommand(JObject json, World world)
		{

			var actorId = json.TryGetFieldValue("actorId")?.ToObject<uint>();
			var groupId = json.TryGetFieldValue("groupId")?.ToObject<int>();
			CPos? location;
			location = null;
			var locationJson = json.TryGetFieldValue("location");
			if (locationJson != null)
			{
				var x = locationJson.TryGetFieldValue("X")?.ToObject<int>();
				var y = locationJson.TryGetFieldValue("Y")?.ToObject<int>();
				if (x != null && y != null)
					location = new CPos((int)x, (int)y);
			}
			var direction = json.TryGetFieldValue("direction")?.ToObject<int>();
			var distance = json.TryGetFieldValue("distance")?.ToObject<int>();
			var attackmove = json.TryGetFieldValue("attackmove")?.ToObject<bool>();

			if (actorId != null)
			{
				if (location != null)
				{
					return MoveActorToLocation((uint)actorId, (CPos)location, attackmove ?? false, world);
				}
				else if (direction != null && distance != null)
				{
					return MoveActorInDirection((uint)actorId, (int)direction, (int)distance, attackmove ?? false, world);
				}
				else
				{
					throw new NotImplementedException("Missing parameters for moveactor command");
				}
			}
			else if (groupId != null)
			{
				if (location != null)
				{
					return MoveGroupToLocation((int)groupId - 1, (CPos)location, attackmove ?? false, world);
				}
				else if (direction != null && distance != null)
				{
					return MoveGroupInDirection((int)groupId - 1, (int)direction, (int)distance, attackmove ?? false, world);
				}
				else
				{
					throw new NotImplementedException("Missing parameters for movegroup command");
				}
			}
			else
			{
				throw new NotImplementedException("Missing parameters for move command");
			}
		}
		public static JObject ActorQueryCommand(JObject json, World world)
		{
			var actorsInfo = world.Actors
				.Where(actor => actor.Owner == world.LocalPlayer && actor.OccupiesSpace != null)
				.Select(actor => new JObject
				{
					["Id"] = actor.ActorID,
					["Type"] = actor.Info.Name,
					["Position"] = new JObject
					{
						["X"] = actor.Location.X,
						["Y"] = actor.Location.Y
					}
				})
				.ToList();

			var result = new JObject
			{
				["status"] = "success",
				["actors"] = new JArray(actorsInfo)
			};

			return result;
		}

		public static string MoveActorInDirection(uint actorId, int direction, int distance, bool isattackmove, World world)
		{
			var actor = world.Actors.FirstOrDefault(a => a.ActorID == actorId);
			if (actor == null)
			{
				TextNotificationsManager.Debug("Actor not found: " + actorId);
				throw new NotImplementedException("Actor not found: " + actorId);
			}

			var directionVector = GetDirectionVector(direction);
			var targetLocation = actor.Location + directionVector * distance;

			if (!world.Map.Contains(targetLocation))
			{
				TextNotificationsManager.Debug("Target location is out of bounads");
				throw new NotImplementedException("Target location is out of bounads");
			}

			actor.QueueActivity(new Move(actor, targetLocation));
			return "Actor Moved";
		}

		public static string MoveActorToLocation(uint actorId, CPos location, bool isattackmove, World world)
		{
			var actor = world.Actors.FirstOrDefault(a => a.ActorID == actorId);
			if (actor == null)
			{
				TextNotificationsManager.Debug("Actor not found: " + actorId);
				throw new NotImplementedException("Actor not found: " + actorId);
			}

			if (!world.Map.Contains(location))
			{
				TextNotificationsManager.Debug("Target location is out of bounads");
				throw new NotImplementedException("Target location is out of bounads");
			}

			actor.QueueActivity(new Move(actor, location));
			return "Actor Moved";
		}

		public static string MoveGroupToLocation(int groupId, CPos location, bool isattackmove, World world)
		{
			var results = new List<string>();
			var group = world.ControlGroups.GetActorsInControlGroup(groupId);
			foreach (var actor in group)
			{
				results.Add(MoveActorToLocation(actor.ActorID, location, isattackmove, world));
			}

			return string.Join("\n", results);
		}

		public static string MoveGroupInDirection(int groupId, int direction, int distance, bool isattackmove, World world)
		{

			var results = new List<string>();
			var group = world.ControlGroups.GetActorsInControlGroup(groupId);

			foreach (var actor in group)
			{
				results.Add(MoveActorInDirection(actor.ActorID, direction, distance, isattackmove, world));
			}
			return string.Join("\n", results);
		}
		static CVec GetDirectionVector(int direction)
		{
			switch (direction)
			{
				case 0: return new CVec(0, -1);  // North
				case 1: return new CVec(1, -1);  // Northeast
				case 2: return new CVec(1, 0);   // East
				case 3: return new CVec(1, 1);   // Southeast
				case 4: return new CVec(0, 1);   // South
				case 5: return new CVec(-1, 1);  // Southwest
				case 6: return new CVec(-1, 0);  // West
				case 7: return new CVec(-1, -1); // Northwest
				default:
					TextNotificationsManager.Debug("Invalid direction: " + direction);
					throw new NotImplementedException("Invalid direction: " + direction);
			}
		}



		public static string StartProdunctionCommand(JObject json, World world)
		{
			var units = json.TryGetFieldValue("units")?.ToObject<List<string>>();
			var player = world.LocalPlayer;
			var ret_str = "";

			if (units == null || units.Count == 0)
			{
				throw new ArgumentException("No units specified for Produnction command");
			}

			foreach (var unitName in units)
			{
				if (!world.Map.Rules.Actors.TryGetValue(unitName, out var unit))
				{
					ret_str += $"Error!! There is no unit named {unitName}!! \n";
					continue;
				}

				var bi = unit.TraitInfo<BuildableInfo>();
				var queue = bi.Queue
			.SelectMany(oneQueue => AIUtils.FindQueues(player, oneQueue))
			.FirstOrDefault();

				if (queue != null)
				{
					world.IssueOrder(Order.StartProduction(queue.Actor, unitName, 1, true, true));
					ret_str += $"{unitName} built.\n";
				}
				else
				{
					ret_str += $"No suitable queue found for unit {unitName}.\n";
				}

			}

			return ret_str;
		}

		public static string CameraMoveCommand(JObject json, World world)
		{
			var direction = json.TryGetFieldValue("direction")?.ToObject<int>();
			var distance = json.TryGetFieldValue("distance")?.ToObject<int>();

			if (direction == null || distance == null)
			{
				return "No direction Or No Distance!!!!!!";
			}

			var directionVector = GetDirectionVector(direction.Value) * distance.Value;
			var worldRenderer = Game.worldRenderer;
			worldRenderer.Viewport.Scroll(new float2(directionVector.X, directionVector.Y), true);

			return $"Camera moved {direction.Value} by {distance.Value} pxs.";
		}

		public void WorldLoaded(World w, WorldRenderer wr)
		{
			world = w;
			if (w.Type == WorldType.Regular && w.CopilotServer != null)
			{
				w.CopilotServer.OnMoveActorCommand += MoveActorCommand;
				w.CopilotServer.QueryActor += ActorQueryCommand;
				w.CopilotServer.OnStartProdunctionCommand += StartProdunctionCommand;
				w.CopilotServer.OnCameraMoveCommand += CameraMoveCommand;
			}
		}
	}
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Traits;
using static OpenRA.GameInformation;

namespace OpenRA.Mods.Common.Commands
{
	[TraitLocation(SystemActors.World)]
	[Desc("Attach this to the world actor.")]
	public class ServerCommandsInfo : TraitInfo<ServerCommands> { }
	public class ServerCommands : IWorldLoaded, ITick
	{
		public static List<Actor> GetTargets(JToken targets, World world, Player player)
		{
			var result = new List<Actor>();

			// 解析参数
			var range = targets["range"]?.ToString() ?? "all";
			var groupIds = targets["groupId"]?.ToObject<List<int>>() ?? new List<int>();
			var types = targets["type"]?.ToObject<List<string>>() ?? new List<string>();

			var actors = world.Actors.Where(a => a.Owner == player);

			// 根据范围筛选
			switch (range)
			{
				case "screen":
					var viewport = Game.worldRenderer.Viewport;
					actors = actors.Where(a => a.OccupiesSpace != null && CopilotsUtils.IsVisibleInViewport(Game.worldRenderer, world.Map.CenterOfCell(a.Location)));
					break;
				case "selected":
					actors = actors.Where(a => world.Selection.Contains(a));
					break;
				case "all":
				default:
					// 不做任何筛选
					break;
			}

			// 根据groupId筛选
			if (groupIds.Count > 0)
			{
				var groupActors = new List<Actor>();
				foreach (var groupId in groupIds)
				{
					groupActors.AddRange(world.ControlGroups.GetActorsInControlGroup(groupId - 1));
				}

				actors = actors.Intersect(groupActors);
			}

			// 根据type筛选
			if (types.Count > 0)
			{
				actors = actors.Where(a => types.Contains(a.Info.Name));
			}

			// 返回符合条件的ActorID
			result.AddRange(actors);

			return result;
		}

		public static string SelectUnitCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var targets = json.TryGetFieldValue("targets");
			var isCombine = json.TryGetFieldValue("isCombine")?.ToObject<int>();
			if (targets == null)
			{
				throw new NotImplementedException("Missing parameters for SelectActor command");
			}

			var actors = GetTargets(targets, world, player);
			if (actors.Count <= 0)
				return "No Actor Selected";
			var newSelection = SelectionUtils.SelectActorsByOwnerAndSelectionClass(actors, new List<Player> { player }, null).ToList();
			world.Selection.Combine(world, newSelection, isCombine > 0, false);
			return "Actor Selected";
		}

		public static string FormGroupCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var targets = json.TryGetFieldValue("targets");
			var groupId = json.TryGetFieldValue("groupId")?.ToObject<int>();
			if (targets == null || groupId == null)
			{
				throw new NotImplementedException("Missing parameters for FormGroupCommand");
			}

			var actors = GetTargets(targets, world, player);
			if (actors.Count <= 0)
				return "No Actor Selected";
			var newSelection = SelectionUtils.SelectActorsByOwnerAndSelectionClass(actors, new List<Player> { player }, null).ToList();
			world.Selection.Combine(world, newSelection, false, false);
			world.ControlGroups.CreateControlGroup(groupId.Value - 1);

			return "Group Formed";
		}

		public static string MoveActorCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var targets = json.TryGetFieldValue("targets");
			if (targets == null)
			{
				throw new NotImplementedException("Missing parameters for FormGroupCommand");
			}

			var actors = GetTargets(targets, world, player);
			if (actors.Count <= 0)
				return "No Actor Selected";
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
			var isAttackMove = json.TryGetFieldValue("isAttackMove")?.ToObject<bool>();
			var isAssaultMove = json.TryGetFieldValue("isAssaultMove")?.ToObject<bool>();

			if (location != null)
			{
				return MoveActorToLocation(actors, (CPos)location, isAttackMove ?? false, isAssaultMove ?? false, world);
			}
			else if (direction != null && distance != null)
			{
				return MoveActorInDirection(actors, (int)direction, (int)distance, isAttackMove ?? false, isAssaultMove ?? false, world);
			}
			else
			{
				throw new NotImplementedException("Missing parameters for moveactor command");
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

		public static string MoveActorInDirection(IEnumerable<Actor> actors, int direction, int distance, bool isAttackMove, bool isAssaultMove, World world)
		{
			var num = 0;
			foreach (var actor in actors)
			{
				var move = actor.TraitOrDefault<IMove>();
				if (move == null)
					continue;
				num++;
				var directionVector = GetDirectionVector(direction);
				var targetLocation = actor.Location + directionVector * distance;

				if (!world.Map.Contains(targetLocation))
				{
					TextNotificationsManager.Debug("Target location is out of bounads");
					throw new NotImplementedException("Target location is out of bounads");
				}

				actor.CancelActivity();
				if (isAttackMove || isAssaultMove)
				{
					actor.QueueActivity(new AttackMoveActivity(actor, () => move.MoveTo(targetLocation, 8, null), isAssaultMove));
				}
				else
				{
					actor.QueueActivity(new Move(actor, targetLocation));
				}
			}

			return $"{num} Actor Moved";
		}

		public static string MoveActorToLocation(IEnumerable<Actor> actors, CPos targetLocation, bool isAttackMove, bool isAssaultMove, World world)
		{
			var num = 0;
			foreach (var actor in actors)
			{
				var move = actor.TraitOrDefault<IMove>();
				if (move == null)
					continue;
				num++;
				actor.CancelActivity();
				if (isAttackMove || isAssaultMove)
				{
					actor.QueueActivity(new AttackMoveActivity(actor, () => move.MoveTo(targetLocation, 8, null), isAssaultMove));
				}
				else
				{
					actor.QueueActivity(new Move(actor, targetLocation));
				}
			}

			return $"{num} Actor Moved";
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
			var orders = json.TryGetFieldValue("units")?.ToObject<List<JToken>>();
			var player = world.LocalPlayer;
			var ret_str = "";

			if (orders == null || orders.Count == 0)
			{
				throw new ArgumentException("No units specified for Produnction command");
			}

			foreach (var order in orders)
			{
				var unitName = order.TryGetFieldValue("unit_type")?.ToObject<string>();
				var quantity = order.TryGetFieldValue("quantity")?.ToObject<int>();
				if (unitName == null || quantity == null)
				{
					throw new NotImplementedException("Missing parameters for StartProdunctionCommand");
				}

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
					world.IssueOrder(Order.StartProduction(queue.Actor, unitName, quantity.Value, true, true));
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
			if (w.Type == WorldType.Regular && w.CopilotServer != null)
			{
				w.CopilotServer.OnMoveActorCommand += MoveActorCommand;
				w.CopilotServer.QueryActor += ActorQueryCommand;
				w.CopilotServer.OnStartProdunctionCommand += StartProdunctionCommand;
				w.CopilotServer.OnCameraMoveCommand += CameraMoveCommand;
				w.CopilotServer.OnSelectUnitCommand += SelectUnitCommand;
				w.CopilotServer.OnFormGroupCommand += FormGroupCommand;
			}
		}

		public void Tick(Actor self)
		{
		}
	}
}

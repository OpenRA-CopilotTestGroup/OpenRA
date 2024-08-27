using System;
using System.Collections.Generic;
using System.Linq;
using ICSharpCode.SharpZipLib.Core;
using System.Numerics;
using System.Reflection;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Orders;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Traits;
using static OpenRA.GameInformation;
using System.Collections;
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

			var actorIds = targets["actorId"]?.ToObject<List<int>>() ?? new List<int>();
			if (actorIds.Count > 0)
			{
				foreach (var actorId in actorIds)
				{
					var actor = world.Actors.FirstOrDefault(a => a.ActorID == actorId);
					if (actor != null)
					{
						result.Add(actor);
					}
				}

				return result;
			}

			// 解析参数
			var range = targets["range"]?.ToString() ?? "all";
			var groupIds = targets["groupId"]?.ToObject<List<int>>() ?? new List<int>();
			var types = targets["type"]?.ToObject<List<string>>() ?? new List<string>();
			var faction = targets["faction"]?.ToString() ?? "己方";
			types = types.ConvertAll(x => CopilotsConfig.GetConfigNameByChinese(x));
			IEnumerable<Actor> actors;
			if (faction == "己方" || faction == "自己" || faction == "我" || faction == "我的")
				actors = world.Actors.Where(a => a.Owner == player && a.OccupiesSpace != null);
			else if (faction == "敌方" || faction == "敌人" || faction == "对面" || faction == "他的" || faction == "他")
				actors = world.Actors.Where(a => a.Owner != player && a.Owner.IsBot && a.OccupiesSpace != null);
			else
				throw new ArgumentException($"Invalid faction: {faction}");

			// 根据范围筛选
			switch (range)
			{
				case "screen":
					var viewport = Game.worldRenderer.Viewport;
					actors = actors.Where(a => CopilotsUtils.IsVisibleInViewport(Game.worldRenderer, world.Map.CenterOfCell(a.Location)));
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

			var restrains = targets["restrain"]?.ToList();
			if (restrains != null)
			{
				foreach (var restrain in restrains)
				{
					var direction = restrain["relativeDirection"]?.ToString();
					var maxNum = restrain["maxNum"]?.ToObject<int>();
					var dis = restrain["distance"]?.ToObject<int>();

					if (direction != null && maxNum.HasValue)
					{
						var directionVector = CopilotsUtils.GetDirectionVector(direction);
						actors = actors.OrderBy(a => -a.Location.X * directionVector.X - a.Location.Y * directionVector.Y);
						actors = actors.Take(maxNum.Value);
					}
					else if (maxNum.HasValue)
					{
						actors = actors.Take(maxNum.Value);
					}
					else if (dis.HasValue)
					{
						var loc = GetLocation(targets["location"]);
						actors = actors.Where(a => Math.Abs(a.Location.X - loc.X) + Math.Abs(a.Location.Y - loc.Y) <= dis.Value);
					}
				}
			}

			// 返回符合条件的ActorID
			result.AddRange(actors);

			return result;
		}

		public static CPos GetLocation(JToken location)
		{
			var x = location["x"]?.ToObject<int>();
			var y = location["y"]?.ToObject<int>();
			if (x != null && y != null)
			{
				return new CPos(x.Value, y.Value);
			}

			throw new NotImplementedException("Missing parameters in \"Location\" for command");
		}

		public static List<Actor> GetTargetsFromJson(JObject json, World world, bool bAllowEmpty = false)
		{
			var player = world.LocalPlayer;
			var targets = json.TryGetFieldValue("targets");
			if (targets == null)
			{
				if (bAllowEmpty)
					return new List<Actor>();
				throw new NotImplementedException("Missing parameters \"Targets\" for command");
			}

			var actors = GetTargets(targets, world, player);
			if (actors.Count == 0 && !bAllowEmpty)
			{
				throw new NotImplementedException("NO Valid Actor.");
			}

			return actors;
		}

		public static CPos? GetLocation(JToken location, World world, Player player)
		{
			if (location == null)
				return null;
			var x = location["x"]?.ToObject<int>();
			var y = location["y"]?.ToObject<int>();
			if (x != null && y != null)
			{
				return new CPos(x.Value, y.Value);
			}

			var targets = location.TryGetFieldValue("targets");
			if (targets == null)
			{
				return null;
				//throw new NotImplementedException("Missing parameters targets for location");
			}

			var sum = new CPos(0, 0);
			var targetActors = GetTargets(targets, world, player);

			if (targetActors.Count == 0)
			{
				return null;
				//throw new NotImplementedException("no actor targets for location");
			}

			foreach (var target in targetActors)
			{
				sum = new CPos(sum.X + target.Location.X, sum.Y + target.Location.Y);
			}

			var count = targetActors.Count;
			var averageLocation = new CPos(sum.X / count, sum.Y / count);

			var direction = location.TryGetFieldValue("direction")?.ToObject<string>();
			var distance = location.TryGetFieldValue("distance")?.ToObject<int>();

			if (direction != null && distance != null)
			{
				averageLocation += CopilotsUtils.GetDirectionVector(direction) * distance.Value;
			}

			return averageLocation;
		}

		public static string SelectUnitCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var isCombine = json.TryGetFieldValue("isCombine")?.ToObject<int>();
			var actors = GetTargetsFromJson(json, world);
			var newSelection = SelectionUtils.SelectActorsByOwnerAndSelectionClass(actors, new List<Player> { player }, null).ToList();
			world.Selection.Combine(world, newSelection, isCombine > 0, false);
			return "Actor Selected";
		}

		public static string FormGroupCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var groupId = json.TryGetFieldValue("groupId")?.ToObject<int>();
			if (groupId == null)
			{
				throw new NotImplementedException("Missing parameters groupId for FormGroupCommand");
			}
			var actors = GetTargetsFromJson(json, world);
			var newSelection = SelectionUtils.SelectActorsByOwnerAndSelectionClass(actors, new List<Player> { player }, null).ToList();
			world.Selection.Combine(world, newSelection, false, false);
			world.ControlGroups.CreateControlGroup(groupId.Value - 1);

			return "Group Formed";
		}

		public static string MoveActorCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var actors = GetTargetsFromJson(json, world);
			CPos? location;
			location = null;
			var locationJson = json.TryGetFieldValue("location");
			if (locationJson != null)
			{
				location = GetLocation(locationJson, world, player);
			}

			var direction = json.TryGetFieldValue("direction")?.ToObject<string>();
			var distance = json.TryGetFieldValue("distance")?.ToObject<int>();
			var isAttackMove = json.TryGetFieldValue("isAttackMove")?.ToObject<int>();
			var isAssaultMove = json.TryGetFieldValue("isAssaultMove")?.ToObject<int>();

			if (location != null)
			{
				return MoveActorToLocation(actors, (CPos)location, isAttackMove > 0, isAssaultMove > 0, world);
			}
			else if (direction != null && distance != null)
			{
				return MoveActorInDirection(actors, direction, distance.Value, isAttackMove > 0, isAssaultMove > 0, world);
			}
			else
			{
				throw new NotImplementedException("Missing parameters for moveactor command");
			}
		}

		public static JObject ActorQueryCommand(JObject json, World world)
		{
			var player = world.LocalPlayer;
			var targets = json.TryGetFieldValue("targets");
			List<Actor> targetActors;
			if (targets == null)
			{
				return null;
				//targetActors = world.Actors.Where(a => a.OccupiesSpace != null).ToList();
			}
			else
			{
				targetActors = GetTargets(targets, world, player);
			}

			var sum = new CPos(0, 0);

			var actorsInfo = targetActors
				.ConvertAll(actor => new JObject
				{
					["id"] = actor.ActorID,
					["type"] = actor.Info.Name,
					["faction"] = actor.Owner == player ? "己方" : "敌方",
					["position"] = new JObject
					{
						["x"] = actor.Location.X,
						["y"] = actor.Location.Y
					}
				});

			var result = new JObject
			{
				//["status"] = "success",
				["actors"] = new JArray(actorsInfo)
			};

			return result;
		}

		public static string MoveActorInDirection(IEnumerable<Actor> actors, string direction, int distance, bool isAttackMove, bool isAssaultMove, World world)
		{
			var num = 0;
			foreach (var actor in actors)
			{
				var move = actor.TraitOrDefault<IMove>();
				if (move == null)
					continue;
				num++;
				var directionVector = CopilotsUtils.GetDirectionVector(direction);
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

		public static string StartProductionCommand(JObject json, World world)
		{
			var orders = json.TryGetFieldValue("units")?.ToObject<List<JToken>>();
			var player = world.LocalPlayer;
			var ret_str = "";

			if (orders == null || orders.Count == 0)
			{
				throw new ArgumentException("No units specified for Produnction command");
			}
			Dictionary<string, int> produceMap = new Dictionary<string, int>();
			foreach (var order in orders)
			{
				var unitName = order.TryGetFieldValue("unit_type")?.ToObject<string>();
				unitName = CopilotsConfig.GetConfigNameByChinese(unitName);
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
					var newWait = Tuple.Create(unitName, quantity.Value);
					produceMap.Add(unitName, quantity.Value);
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
			var worldRenderer = Game.worldRenderer;
			var direction = json.TryGetFieldValue("direction")?.ToObject<string>();
			var distance = json.TryGetFieldValue("distance")?.ToObject<int>();
			var locationToken = json.TryGetFieldValue("location");
			var location = GetLocation(locationToken, world, world.LocalPlayer);
			if ((direction == null || distance == null) && location == null)
			{
				return "No direction Or No Distance Or No Location !!!!!!";
			}

			var directionVector = new CVec(0, 0);
			if (direction != null && distance != null)
				directionVector = CopilotsUtils.GetDirectionVector(direction) * distance.Value;
			if (location != null)
			{
				worldRenderer.Viewport.Center(world.Map.CenterOfCell(location.Value + directionVector));
				return $"Camera moved to {location.Value + directionVector}";
			}

			directionVector *= world.Map.Grid.TileSize.Width;
			//CopilotsUtils.GetDirectionVector(direction) * distance.Value * world.Map.Grid.TileSize.Width;
			worldRenderer.Viewport.Scroll(new float2(directionVector.X, directionVector.Y), true);

			return $"Camera moved {direction} by {distance.Value}.";
		}

		public static JObject TileInfoQueryCommand(JObject json, World world)
		{
			var compressLevel = json.TryGetFieldValue("compressNum")?.ToObject<int>() ?? 5;
			var actors = GetTargetsFromJson(json, world);
			var actor = actors.Last();

			var tileInfo = GetTileInfo(world, actor);
			var compressedTileInfo = CompressTileInfo(tileInfo, compressLevel);

			var jArrayTileInfo = new JArray();
			foreach (var row in compressedTileInfo)
			{
				var jArrayRow = new JArray(row);
				jArrayTileInfo.Add(jArrayRow);
			}

			var result = new JObject
			{
				["tileHeight"] = compressedTileInfo.Count,
				["tileWidth"] = compressedTileInfo.Last().Count,
				["tiles"] = jArrayTileInfo
			};

			return result;
		}

		static List<List<byte>> GetTileInfo(World world, Actor actor)
		{
			var map = world.Map;
			var tileInfo = new List<List<byte>>();
			for (var x = 0; x < map.Bounds.Width; x++)
			{
				var tempList = new List<byte>();
				for (var y = 0; y < map.Bounds.Height; y++)
				{
					var pos = new CPos(x, y);
					//var target = Target.FromCell(world, pos);
					var mobile = actor.TraitOrDefault<Mobile>();
					if (mobile == null)
						return null;

					var pathFinder = actor.World.WorldActor.Trait<PathFinder>();
					var locomotor = mobile.Locomotor;
					var canMove = pathFinder.PathExistsForLocomotor(locomotor, actor.Location, pos);
					//	var orders = actor.TraitsImplementing<IIssueOrder>()
					//.SelectMany(trait => trait.Orders.Select(x => new { Trait = trait, Order = x }))
					//.Where(order => order.Order. == "Move" || order.OrderName == "AttackMove")
					//.Select(x => x)
					//.OrderByDescending(x => x.Order.OrderPriority)
					//.ToList();
					//	var CanMove = false;
					//	foreach (var o in orders)
					//	{
					//		var localModifiers = TargetModifiers.None;
					//		string cursor = null;
					//		if (o.Order.CanTarget(actor, target, ref localModifiers, ref cursor))
					//			CanMove = true;
					//	}

					tempList.Add((byte)(canMove ? 0 : 1));
					//var terrainTile = map.Tiles[new MPos(x, y)];

				}
				tileInfo.Add(tempList);
			}
			return tileInfo;
		}

		static List<List<byte>> CompressTileInfo(List<List<byte>> tileInfo, int compressLevel)
		{
			var width = tileInfo.Count;
			var height = tileInfo[0].Count;
			var compressedWidth = (width + compressLevel - 1) / compressLevel;
			var compressedHeight = (height + compressLevel - 1) / compressLevel;

			var compressedTileInfo = new List<List<byte>>();

			for (var x = 0; x < compressedWidth; x++)
			{
				var compressedRow = new List<byte>();
				for (var y = 0; y < compressedHeight; y++)
				{
					var count = 0;
					var total = 0;

					for (var i = 0; i < compressLevel; i++)
					{
						for (var j = 0; j < compressLevel; j++)
						{
							var xi = x * compressLevel + i;
							var yj = y * compressLevel + j;
							if (xi < width && yj < height)
							{
								total++;
								if (tileInfo[xi][yj] == 1)
								{
									count++;
								}
							}
						}
					}

					// 如果1的数量超过50%，则压缩后的格子为1，否则为0
					compressedRow.Add((byte)(count > total / 2 ? 1 : 0));
				}
				compressedTileInfo.Add(compressedRow);
			}

			return compressedTileInfo;
		}

		public static string MoveActorOnTilePathCommand(JObject json, World world)
		{
			var actors = GetTargetsFromJson(json, world);
			var compressLevel = json.TryGetFieldValue("compressNum")?.ToObject<int>() ?? 5;
			var tilePathArr = json.TryGetFieldValue("pathTiles")?.ToList();
			if (tilePathArr == null)
			{
				throw new NotImplementedException("Missing parameters PathTiles for Command");
			}

			var tileInfo = GetTileInfo(world, actors.Last());
			var compressedTileInfo = CompressTileInfo(tileInfo, compressLevel);

			var path = new List<CPos>();

			// 移除tilePathArr第一个格子
			tilePathArr.RemoveAt(0);
			foreach (var tile in tilePathArr)
			{
				var tileCoords = tile.ToObject<int[]>();
				if (tileCoords == null || tileCoords.Length != 2)
				{
					throw new ArgumentException("Invalid tile coordinates.");
				}

				var x = tileCoords[0];
				var y = tileCoords[1];

				if (x < 0 || x >= compressedTileInfo.Count || y < 0 || y >= compressedTileInfo[x].Count)
				{
					throw new ArgumentException($"Tile coordinates ({x}, {y}) are out of bounds.");
				}

				if (compressedTileInfo[x][y] == 1)
				{
					throw new ArgumentException($"Tile ({x}, {y}) is an obstacle.");
				}

				var closestEmptyPoint = FindClosestEmptyPoint(tileInfo, x * compressLevel, y * compressLevel);
				if (closestEmptyPoint.HasValue)
				{
					path.Add(closestEmptyPoint.Value);
				}
				else
				{
					throw new Exception($"No empty tile found near ({x}, {y}).");
				}
			}

			// Issue multi-point move order to all actors
			foreach (var actor in actors)
			{
				actor.CancelActivity();

				// Queue the move orders
				foreach (var waypoint in path)
				{
					actor.QueueActivity(new Move(actor, waypoint));
				}
			}

			return "Actor Moved";
		}

		static CPos? FindClosestEmptyPoint(List<List<byte>> map, int x, int y)
		{
			var centerX = x + 2;
			var centerY = y + 2;
			var minDistance = int.MaxValue;
			CPos? closestPoint = null;

			for (var i = 0; i < 5; i++)
			{
				for (var j = 0; j < 5; j++)
				{
					var checkX = x + i;
					var checkY = y + j;

					if (checkX >= 0 && checkX < map.Count && checkY >= 0 && checkY < map[0].Count && map[checkX][checkY] == 0)
					{
						var distance = Math.Abs(checkX - centerX) + Math.Abs(checkY - centerY);
						if (distance < minDistance)
						{
							minDistance = distance;
							closestPoint = new CPos(checkX, checkY);
						}
					}
				}
			}

			return closestPoint;
		}

		public static JObject PathQueryCommand(JObject json, World world)
		{
			var actors = GetTargetsFromJson(json, world);
			var actor = actors.Last();
			var destination = json.TryGetFieldValue("destination");
			if (destination == null)
			{
				throw new NotImplementedException("Missing parameters destination for Command");
			}

			var desPos = GetLocation(destination);

			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;
			var pathFinder = actor.World.WorldActor.Trait<PathFinder>();
			var locomotor = mobile.Locomotor;
			var path = pathFinder.FindPathToTargetCell(actor, new[] { actor.Location }, desPos, BlockedByActor.None);

			var pathArray = new JArray();
			foreach (var cpos in path)
			{
				pathArray.Add(new JObject
				{
					["x"] = cpos.X,
					["y"] = cpos.Y
				});
			}

			var result = new JObject
			{
				["path"] = pathArray
			};

			return result;
		}

		public void WorldLoaded(World w, WorldRenderer wr)
		{
			if (w.Type == WorldType.Regular && w.CopilotServer != null)
			{
				w.CopilotServer.OnMoveActorCommand += MoveActorCommand;
				w.CopilotServer.OnMoveActorOnTilePathCommand += MoveActorOnTilePathCommand;
				w.CopilotServer.QueryActor += ActorQueryCommand;
				w.CopilotServer.QueryTile += TileInfoQueryCommand;
				w.CopilotServer.QueryPath += PathQueryCommand;
				w.CopilotServer.OnStartProductionCommand += StartProductionCommand;
				w.CopilotServer.OnCameraMoveCommand += CameraMoveCommand;
				w.CopilotServer.OnSelectUnitCommand += SelectUnitCommand;
				w.CopilotServer.OnFormGroupCommand += FormGroupCommand;
				CopilotsConfig.LoadConfig();
			}
		}

		public void Tick(Actor self)
		{
		}
	}
}

using System;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Activities;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Commands
{
	[TraitLocation(SystemActors.World)]
	[Desc("Attach this to the world actor.")]
	public class ServerCommandsInfo : TraitInfo<ServerCommands> { }
	public class ServerCommands : IWorldLoaded
	{
		World world;
		public static void MoveActorCommand(string arg, World world)
		{
			var arguments = arg.Split(' ');
			if (arguments.Length != 3)
			{
				TextNotificationsManager.Debug("Invalid number of arguments. Usage: /moveactor <actorId> <direction> <distance>");
				return;
			}

			if (!uint.TryParse(arguments[0], out var actorId))
			{
				TextNotificationsManager.Debug("Invalid ActorID. ActorID must be an uint.");
				return;
			}


			if (!int.TryParse(arguments[1], out var direction))
			{
				TextNotificationsManager.Debug("Invalid direction. Direction must be an integer between 0 and 7.");
				return;
			}

			if (!int.TryParse(arguments[2], out var distance))
			{
				TextNotificationsManager.Debug("Invalid distance. Distance must be an integer.");
				return;
			}

			MoveActor(actorId, direction, distance, world);
		}

		public static void MoveActor(uint actorId, int direction, int distance, World world)
		{
			var actor = world.Actors.FirstOrDefault(a => a.ActorID == actorId);
			if (actor == null)
			{
				TextNotificationsManager.Debug("Actor not found: " + actorId);
				return;
			}

			var directionVector = GetDirectionVector(direction);
			var targetLocation = actor.Location + directionVector * distance;

			if (!world.Map.Contains(targetLocation))
			{
				TextNotificationsManager.Debug("Target location is out of bounads");
				return;
			}

			actor.QueueActivity(new Move(actor, targetLocation));
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
				default: throw new ArgumentException("Invalid direction: " + direction);
			}
		}

		public void WorldLoaded(World w, WorldRenderer wr)
		{
			world = w;
			if (w.Type == WorldType.Regular)
			{
				w.CopilotServer.OnMoveActorCommand += MoveActorCommand;
			}
		}
	}
}

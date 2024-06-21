#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Common
{

	public static class CopilotsUtils
	{
		public static void TryBuild(World world, string buildingName, Actor building, ProductionQueue queue)
		{
			var type = BuildingType.Building;
			CPos? location = null;
			var actorVariant = 0;
			var orderString = "PlaceBuilding";
			var player = building.Owner;
			var actorInfo = world.Map.Rules.Actors[buildingName];

			var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (bi == null)
				return;
			(CPos? Location, int Variant) FindPos(CPos center, CPos target, int minRange, int maxRange)
			{
				var actorVariant = 0;
				var buildingVariantInfo = actorInfo.TraitInfoOrDefault<PlaceBuildingVariantsInfo>();
				var variantActorInfo = actorInfo;
				var vbi = bi;

				var cells = world.Map.FindTilesInAnnulus(center, minRange, maxRange);

				// Sort by distance to target if we have one
				if (center != target)
				{
					cells = cells.OrderBy(c => (c - target).LengthSquared);

					// Rotate building if we have a Facings in buildingVariantInfo.
					// If we don't have Facings in buildingVariantInfo, use a random variant
					if (buildingVariantInfo?.Actors != null)
					{
						if (buildingVariantInfo.Facings != null)
						{
							var vector = world.Map.CenterOfCell(target) - world.Map.CenterOfCell(center);

							// The rotation Y point to upside vertically, so -Y = Y(rotation)
							var desireFacing = new WAngle(WAngle.ArcSin((int)((long)Math.Abs(vector.X) * 1024 / vector.Length)).Angle);
							if (vector.X > 0 && vector.Y >= 0)
								desireFacing = new WAngle(512) - desireFacing;
							else if (vector.X < 0 && vector.Y >= 0)
								desireFacing = new WAngle(512) + desireFacing;
							else if (vector.X < 0 && vector.Y < 0)
								desireFacing = -desireFacing;

							for (int i = 0, e = 1024; i < buildingVariantInfo.Facings.Length; i++)
							{
								var minDelta = Math.Min((desireFacing - buildingVariantInfo.Facings[i]).Angle, (buildingVariantInfo.Facings[i] - desireFacing).Angle);
								if (e > minDelta)
								{
									e = minDelta;
									actorVariant = i;
								}
							}
						}
						else
							actorVariant = world.LocalRandom.Next(buildingVariantInfo.Actors.Length + 1);
					}
				}
				else
				{
					cells = cells.Shuffle(world.LocalRandom);

					if (buildingVariantInfo?.Actors != null)
						actorVariant = world.LocalRandom.Next(buildingVariantInfo.Actors.Length + 1);
				}

				if (actorVariant != 0)
				{
					variantActorInfo = world.Map.Rules.Actors[buildingVariantInfo.Actors[actorVariant - 1]];
					vbi = variantActorInfo.TraitInfoOrDefault<BuildingInfo>();
				}

				foreach (var cell in cells)
				{
					if (!world.CanPlaceBuilding(cell, variantActorInfo, vbi, null))
						continue;

					if (!vbi.IsCloseEnoughToBase(world, player, variantActorInfo, cell))
						continue;

					return (cell, actorVariant);
				}

				return (null, 0);
			}

			(CPos? Location, int Variant) ChooseBuildLocation(string actorType, bool distanceToBaseIsImportant, BuildingType type)
			{
				var actorInfo = world.Map.Rules.Actors[actorType];
				var facts = new ActorIndex.OwnerAndNamesAndTrait<Transforms>(world, new List<string> { "fact" }, player);
				if (facts.Actors.Count == 0)
					return (null, 0);
				var baseCenter = facts.Actors.FirstOrDefault().Location;
				const int MinimumDefenseRadius = 0;
				const int MaximumDefenseRadius = 20;
				const int MinBaseRadius = 0;
				const int MaxBaseRadius = 20;
				const int MaxResourceCellsToCheck = 20;
				switch (type)
				{
					case BuildingType.Defense:

						// Build near the closest enemy structure
						var closestEnemy = world.ActorsHavingTrait<Building>()
							.Where(a => !a.Disposed && player.RelationshipWith(a.Owner) == PlayerRelationship.Enemy)
							.ClosestToIgnoringPath(world.Map.CenterOfCell(baseCenter));

						var targetCell = closestEnemy != null ? closestEnemy.Location : baseCenter;

						return FindPos(baseCenter, targetCell, MinimumDefenseRadius, MaximumDefenseRadius);
					case BuildingType.Refinery:

						var resourceLayer = world.WorldActor.TraitOrDefault<IResourceLayer>();
						// Try and place the refinery near a resource field
						if (resourceLayer != null)
						{
							var nearbyResources = world.Map.FindTilesInAnnulus(baseCenter, MinBaseRadius, MaxBaseRadius)
								.Where(a => resourceLayer.GetResource(a).Type != null)
								.Shuffle(world.LocalRandom).Take(MaxResourceCellsToCheck);

							foreach (var r in nearbyResources)
							{
								var found = FindPos(baseCenter, r, MinBaseRadius, MaxBaseRadius);
								if (found.Location != null)
									return found;
							}
						}

						// Try and find a free spot somewhere else in the base
						return FindPos(baseCenter, baseCenter, MinBaseRadius, MaxBaseRadius);

					case BuildingType.Building:
						return FindPos(baseCenter, baseCenter, MinBaseRadius,
							distanceToBaseIsImportant ? MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange);
				}

				// Can't find a build location
				return (null, 0);
			}

			// Check if Building is a plug for other Building
			var plugInfo = actorInfo.TraitInfoOrDefault<PlugInfo>();

			if (plugInfo != null)
			{
				var possibleBuilding = world.ActorsWithTrait<Pluggable>().FirstOrDefault(a =>
					a.Actor.Owner == player && a.Trait.AcceptsPlug(plugInfo.Type));

				if (possibleBuilding.Actor != null)
				{
					orderString = "PlacePlug";
					location = possibleBuilding.Actor.Location + possibleBuilding.Trait.Info.Offset;
				}
			}
			else
			{
				var defenseTypes = new HashSet<string> { "gtwr", "gun", "atwr", "obli", "sam" };
				var refineryTypes = new HashSet<string> { "proc" };
				// Check if Building is a defense and if we should place it towards the enemy or not.
				if (defenseTypes.Contains(actorInfo.Name))
					type = BuildingType.Defense;
				else if (refineryTypes.Contains(actorInfo.Name))
					type = BuildingType.Refinery;

				(location, actorVariant) = ChooseBuildLocation(buildingName, true, type);
			}

			if (location != null)
			{
				world.IssueOrder(new Order(orderString, player.PlayerActor, Target.FromCell(world, location.Value), false)
				{
					// Building to place
					TargetString = buildingName,

					// Actor variant will always be small enough to safely pack in a CPos
					ExtraLocation = new CPos(actorVariant, 0),

					// Actor ID to associate the placement with
					ExtraData = queue.Actor.ActorID,
					SuppressVisualFeedback = true
				});
			}
		}
	}
}

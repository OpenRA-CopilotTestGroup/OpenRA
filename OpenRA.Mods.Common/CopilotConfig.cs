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
using System.IO;
using System.Linq;

namespace OpenRA.Mods.Common
{
	public static class CopilotsConfig
	{
		static Dictionary<string, List<string>> configNameToChinese;
		static Dictionary<string, string> chineseToConfigName;

		public static void LoadConfig()
		{

			var parentDirectory = Path.GetDirectoryName(AppDomain.CurrentDomain.BaseDirectory);
			parentDirectory = Path.GetDirectoryName(parentDirectory);

			// 这里指定 Copilot.yaml 文件的相对路径
			var filePath = Path.Combine(parentDirectory, "mods", "common", "Copilot.yaml");

			if (!File.Exists(filePath))
			{
				Console.WriteLine($"文件路径无效: {filePath}");
				return;
			}

			var yamlNodes = MiniYaml.FromFile(filePath);
			var unitsNode = yamlNodes.FirstOrDefault(node => node.Key == "units").Value;

			configNameToChinese = new Dictionary<string, List<string>>();
			chineseToConfigName = new Dictionary<string, string>();

			foreach (var node in unitsNode.Nodes)
			{
				var configName = node.Key;
				var chineseNames = node.Value.Nodes.Select(n => n.Key).ToList();

				configNameToChinese[configName] = chineseNames;
				foreach (var chineseName in chineseNames)
				{
					chineseToConfigName[chineseName] = configName;
				}
			}
		}

		public static string GetConfigNameByChinese(string chineseName)
		{
			var ret = chineseToConfigName.TryGetValue(chineseName, out var configName) ? configName : null;
			if (ret == null)
			{
				Console.WriteLine($"未知单位: {chineseName}");
			}

			return ret;
		}

		public static List<string> GetChineseByConfigName(string configName)
		{
			return configNameToChinese.TryGetValue(configName, out var chineseNames) ? chineseNames : null;
		}

	}
}

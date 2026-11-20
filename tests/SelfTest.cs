using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

namespace GoHMM
{
    static class SelfTest
    {
        static int failed = 0;
        static StringBuilder log = new StringBuilder();

        static void Check(string name, bool ok, string detail)
        {
            log.AppendLine((ok ? "PASS  " : "FAIL  ") + name + (detail != null ? "   [" + detail + "]" : ""));
            if (!ok) failed++;
        }

        static void Main(string[] args)
        {
            string home = args.Length > 0 ? args[0] : ".";
            Directory.CreateDirectory(home);
            string source = args.Length > 1 ? args[1] : null;

            // 1) 真实 options.set 解析
            string work = Path.Combine(home, "options.set");
            if (source != null && File.Exists(source)) File.Copy(source, work, true);

            var before = OptionsFile.ReadActive(work);
            Check("读取现有启用列表", before.Count == 4, string.Join(",", before.ToArray()));

            string original = File.ReadAllText(work, Encoding.UTF8);
            Check("保留其它设置(adapter)", original.Contains("adapter"), null);

            // 2) 写入新列表并回读
            var wanted = new List<string> { "mod_3833108640", "mod_2829744930", "mod_2707749899" };
            OptionsFile.WriteActive(work, wanted);
            string after = File.ReadAllText(work, Encoding.UTF8);
            var readBack = OptionsFile.ReadActive(work);
            Check("写入后回读一致", readBack.SequenceEqual(wanted), string.Join(",", readBack.ToArray()));
            Check("写入后其它设置仍在", after.Contains("adapter") && after.Contains("userName"), null);
            Check("大括号平衡", CountChar(after, '{') == CountChar(after, '}'), CountChar(after, '{') + "/" + CountChar(after, '}'));

            string firstModsLine = null;
            foreach (var l in after.Split('\n'))
            {
                if (l.TrimStart().StartsWith("{mods")) { firstModsLine = l.TrimEnd('\r'); break; }
            }
            Check("mods 块缩进未被破坏", firstModsLine == "\t{mods", firstModsLine == null ? "not found" : firstModsLine.Replace("\t", "->"));
            Check("只产生一个 mods 块", CountOccurrences(after, "{mods") == 1, CountOccurrences(after, "{mods").ToString());

            // 3) 重复写入（幂等）
            OptionsFile.WriteActive(work, wanted);
            var readBack2 = OptionsFile.ReadActive(work);
            Check("重复写入幂等", readBack2.SequenceEqual(wanted), null);

            // 4) 清空
            OptionsFile.WriteActive(work, new List<string>());
            var empty = OptionsFile.ReadActive(work);
            string emptyText = File.ReadAllText(work, Encoding.UTF8);
            Check("清空后为空", empty.Count == 0, null);
            Check("清空后结构仍完整", CountChar(emptyText, '{') == CountChar(emptyText, '}') && emptyText.Contains("adapter"), null);

            // 5) 没有 mods 块的 options.set（CRLF）
            string bare = Path.Combine(home, "bare.set");
            string bareSource = "{options\r\n\t{sound\r\n\t\t{volume 80}\r\n\t}\r\n}\r\n";
            File.WriteAllText(bare, bareSource, new UTF8Encoding(false));
            OptionsFile.WriteActive(bare, new List<string> { "mod_123", "mod_abc" });
            var bareRead = OptionsFile.ReadActive(bare);
            string bareText = File.ReadAllText(bare);
            Check("无 mods 块时自动插入", bareRead.SequenceEqual(new List<string> { "mod_123", "mod_abc" }), string.Join(",", bareRead.ToArray()));
            Check("插入后括号平衡", CountChar(bareText, '{') == CountChar(bareText, '}'), null);
            Check("插入后保留 CRLF", bareText.Contains("\r\n") && !bareText.Contains("\r\r\n"), null);

            // 6) mod.info 解析
            string shop = args.Length > 2 ? args[2] : null;
            if (shop != null && Directory.Exists(shop))
            {
                var mods = Catalog.Scan(shop, null, "1.067.0");
                Check("扫描创意工坊", mods.Count >= 19, "count=" + mods.Count);
                int named = mods.Count(m => !string.IsNullOrEmpty(m.Name) && !m.Name.Contains("未识别"));
                Check("解析出模组名", named >= 18, "named=" + named);
                var withDesc = mods.Count(m => !string.IsNullOrEmpty(m.Desc));
                Check("解析出描述", withDesc >= 15, "withDesc=" + withDesc);
                var broken = mods.Where(m => m.Broken).ToList();
                Check("识别损坏模组", broken.Count >= 1, string.Join(",", broken.Select(b => b.Id).ToArray()));

                // 7) 冲突扫描
                int total;
                var conf = ConflictScanner.Scan(mods.Take(6).ToList(), out total);
                Check("冲突扫描可运行", total > 0, "files=" + total + " conflicts=" + conf.Count);

                var enabled4 = mods.Where(m => m.Id == "3824464151" || m.Id == "2978877382"
                    || m.Id == "3833108640" || m.Id == "3832853088").ToList();
                int total4;
                var conf4 = ConflictScanner.Scan(enabled4, out total4);
                bool noModInfo = true;
                foreach (var g in conf4) if (g.Path.EndsWith("mod.info", StringComparison.OrdinalIgnoreCase)) noModInfo = false;
                Check("mod.info 不再算文件冲突", enabled4.Count == 4 && conf4.Count == 0 && noModInfo,
                    "mods=" + enabled4.Count + " conflicts=" + conf4.Count + " files=" + total4);
            }

            // 8) 分享码
            var ids3 = new List<string> { "mod_2707749899", "mod_2829744930", "mod_3295913567" };
            string code = ShareCode.Encode("测试配置", ids3);
            string err;
            var dec = ShareCode.Decode(code, out err);
            Check("分享码往返一致", dec != null && dec.Ids.SequenceEqual(ids3) && dec.Name == "测试配置", err);

            string pyCode = "eJyrVspLzE1VslJQera1+8X6qS9be5/vXaeko6CUm59SDBSPBjHijcwNzM1NLC0sLaFS8UYWRpbmJiaWxgYwEWMjS1NLQ2NTM3Ol2FoAkFEb8Q==";
            var dec2 = ShareCode.Decode(pyCode, out err);
            Check("能解旧版 zlib 分享码", dec2 != null && dec2.Ids.Count == 3 && dec2.Ids[0] == "mod_2707749899", err);

            var plain = Convert.ToBase64String(Encoding.UTF8.GetBytes("{\"mods\":[\"2829744930\",\"mod_3143336404\"]}"));
            var dec3 = ShareCode.Decode(plain, out err);
            Check("能解未压缩的分享码", dec3 != null && dec3.Ids.Count == 2 && dec3.Ids[0] == "mod_2829744930", err);

            var dec4 = ShareCode.Decode("GOH1:" + code, out err);
            Check("带前缀也能导入", dec4 != null && dec4.Ids.Count == 3, err);

            var bad = ShareCode.Decode("这不是分享码", out err);
            Check("坏码给出错误提示", bad == null && !string.IsNullOrEmpty(err), err);

            // 9) 分享码带模组名（方便对方看到缺的是哪个）
            var titles = new Dictionary<string, string>();
            titles["mod_2707749899"] = "Mount everything";
            string code2 = ShareCode.Encode("带名字", new List<string> { "mod_2707749899", "mod_1111111111" }, titles);
            var dec5 = ShareCode.Decode(code2, out err);
            Check("分享码携带模组名", dec5 != null && dec5.Titles.ContainsKey("mod_2707749899") && dec5.Titles["mod_2707749899"] == "Mount everything", err);

            log.AppendLine();
            log.AppendLine(failed == 0 ? "ALL PASSED" : ("FAILED: " + failed));
            File.WriteAllText(Path.Combine(home, "selftest.log"), log.ToString(), new UTF8Encoding(false));
        }

        static int CountChar(string s, char c) { int n = 0; foreach (char x in s) if (x == c) n++; return n; }
        static int CountOccurrences(string s, string sub)
        {
            int n = 0, i = 0;
            while ((i = s.IndexOf(sub, i, StringComparison.Ordinal)) >= 0) { n++; i += sub.Length; }
            return n;
        }
    }
}

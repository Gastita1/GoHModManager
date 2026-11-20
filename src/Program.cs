using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;

namespace GoHMM
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            if (args.Length >= 3 && args[0] == "--scan")
            {
                RunScan(args[1], args);
                return;
            }
            try
            {
                Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
                Application.ThreadException += delegate(object s2, System.Threading.ThreadExceptionEventArgs e2)
                {
                    AppConfig.Log("UI异常: " + e2.Exception);
                    MessageBox.Show(e2.Exception.ToString(), "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
                };
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new MainForm());
            }
            catch (Exception ex)
            {
                AppConfig.Log("崩溃: " + ex);
                MessageBox.Show(ex.ToString(), "启动失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        // 命令行冲突检测：--scan 输出文件 模组目录1 模组目录2 ...
        static void RunScan(string output, string[] args)
        {
            var mods = new List<ModEntry>();
            for (int i = 2; i < args.Length; i++)
            {
                string d = args[i];
                if (!Directory.Exists(d)) continue;
                var m = new ModEntry();
                m.Dir = Path.GetFullPath(d);
                m.Folder = Path.GetFileName(m.Dir);
                m.Name = m.Folder;
                mods.Add(m);
            }
            int total;
            var groups = ConflictScanner.Scan(mods, out total);
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("mods: " + mods.Count + " | files: " + total + " | conflicts: " + groups.Count);
            foreach (var g in groups)
            {
                sb.AppendLine(g.Path);
                foreach (var m in g.Mods) sb.AppendLine("    " + m.Name);
            }
            File.WriteAllText(output, sb.ToString());
        }
    }
}

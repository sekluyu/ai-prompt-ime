// MIT License. See the repository LICENSE for copyright and development credits.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;

internal static class InstallLauncher
{
    // Quote one argument according to Windows command-line parsing rules.
    private static string Quote(string value)
    {
        var result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in value)
        {
            if (c == '\\') { slashes++; continue; }
            result.Append('\\', c == '"' ? slashes * 2 + 1 : slashes);
            result.Append(c);
            slashes = 0;
        }
        result.Append('\\', slashes * 2);
        return result.Append('"').ToString();
    }

    private static bool HasPython3(string executable, string prefix)
    {
        try
        {
            var info = new ProcessStartInfo(executable,
                prefix + "-c \"import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)\"");
            info.UseShellExecute = false;
            info.CreateNoWindow = true;
            info.RedirectStandardOutput = true;
            info.RedirectStandardError = true;
            using (var process = Process.Start(info))
            {
                process.StandardOutput.ReadToEnd();
                process.StandardError.ReadToEnd();
                process.WaitForExit();
                return process.ExitCode == 0;
            }
        }
        catch (System.ComponentModel.Win32Exception) { return false; }
    }

    private static int Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        int result = 1;
        try
        {
            string folder = AppDomain.CurrentDomain.BaseDirectory;
            string script = Path.Combine(folder, "tools", "install.py");
            if (!File.Exists(script))
                throw new FileNotFoundException("请先完整解压安装包，保留 EXE、tools 和 rime 的相对位置。", script);
            Console.WriteLine("AI 绘画提示词：Windows 小狼毫（Rime）扩展方案安装器");
            Console.WriteLine("请先安装小狼毫。此程序需要 Python 3，只安装方案文件，不安装小狼毫。\n");
            string executable, prefix;
            if (HasPython3("py", "-3 ")) { executable = "py"; prefix = "-3 "; }
            else if (HasPython3("python", "")) { executable = "python"; prefix = ""; }
            else throw new InvalidOperationException("未找到可用的 Python 3。请安装 Python 3 并启用 PATH，然后重新运行。也可用 Python 3 执行 tools/install.py。");
            var arguments = new StringBuilder(prefix + Quote(script));
            foreach (string arg in args) arguments.Append(" ").Append(Quote(arg));
            var info = new ProcessStartInfo(executable, arguments.ToString());
            info.UseShellExecute = false;
            info.WorkingDirectory = folder;
            info.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            using (var process = Process.Start(info))
            {
                process.WaitForExit();
                result = process.ExitCode;
            }
            if (result == 0 && args.Length == 0)
                Console.WriteLine("\n方案文件安装完成。请右键托盘小狼毫 → 重新部署，再按 F4 选择“绘画提示词”。");
            else if (result != 0)
                Console.Error.WriteLine("\n安装未完成，请保留上方错误信息并查看 docs/安装与回滚.md。");
        }
        catch (Exception error) { Console.Error.WriteLine(error.Message); }
        if (args.Length == 0 && !Console.IsInputRedirected)
        {
            Console.WriteLine("\n按任意键关闭。");
            Console.ReadKey(true);
        }
        return result;
    }
}

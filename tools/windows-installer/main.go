// MIT License. Development: GPT (Codex) and DeepSeek. See LICENSE.
package main

import (
	"archive/zip"
	"bufio"
	"bytes"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"syscall"
	"time"
	"unicode/utf8"
)

// The release builder stores the selected dictionary and notices in a standard ZIP.
//
//go:embed resources.zip
var resourceArchive []byte

var bundled fs.FS
var bundleError error

func init() {
	bundled, bundleError = zip.NewReader(bytes.NewReader(resourceArchive), int64(len(resourceArchive)))
}

var version = "0.2.8"
var variant = "default"
var schemeFiles = []string{"booru.schema.yaml", "booru.dict.yaml", "booru.tsv", "booru.annotations.tsv", "lua/booru_filter.lua"}

type backupFile struct {
	Name            string `json:"name"`
	Existed         bool   `json:"existed"`
	InstalledSHA256 string `json:"installed_sha256,omitempty"`
}

type manifest struct {
	FormatVersion    int          `json:"format_version,omitempty"`
	UserDir          string       `json:"user_dir"`
	Files            []backupFile `json:"files"`
	CreatedAt        string       `json:"created_at"`
	PreviousManifest *string      `json:"previous_manifest"`
}

func managedFiles() []string {
	return append(append([]string{}, schemeFiles...), "default.custom.yaml")
}

func updatedConfig(text string) (string, error) {
	if regexp.MustCompile(`(?m)^\s*-\s*\{\s*schema:\s*['"]?booru['"]?\s*\}\s*(?:#.*)?$`).MatchString(text) {
		return text, nil
	}
	newline := "\n"
	if strings.Contains(text, "\r\n") {
		newline = "\r\n"
	}
	matches := regexp.MustCompile(`(?m)^  schema_list:[ \t]*(?:#[^\r\n]*)?(?:\r?\n|$)`).FindAllStringIndex(text, -1)
	if len(matches) == 1 {
		end := matches[0][1]
		prefix := text[:end]
		if !strings.HasSuffix(prefix, "\n") {
			prefix += newline
		}
		return prefix + "    - {schema: booru}" + newline + text[end:], nil
	}
	if strings.TrimSpace(text) == "" {
		return "patch:" + newline + "  schema_list/+:" + newline + "    - {schema: booru}" + newline, nil
	}
	patches := regexp.MustCompile(`(?m)^patch:[ \t]*(?:\r?\n|$)`).FindAllStringIndex(text, -1)
	if len(patches) == 1 && !strings.Contains(text, "schema_list") {
		end := patches[0][1]
		prefix := text[:end]
		if !strings.HasSuffix(prefix, "\n") {
			prefix += newline
		}
		return prefix + "  schema_list/+:" + newline + "    - {schema: booru}" + newline + text[end:], nil
	}
	return "", errors.New("Unrecognized default.custom.yaml layout; no files changed. 请保留现有配置，按安装说明手工加入 booru 后重试。")
}

func digest(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func write(path string, data []byte) error {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	return os.WriteFile(path, data, 0644)
}

func copyFile(source, target string) error {
	data, err := os.ReadFile(source)
	if err != nil {
		return err
	}
	return write(target, data)
}

func saveManifest(path string, value manifest) error {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	return write(path, append(data, '\n'))
}

func install(user string) (string, error) {
	user, err := filepath.Abs(user)
	if err != nil {
		return "", err
	}
	// Read all embedded files and validate the config before changing user files.
	sources := make(map[string][]byte)
	for _, name := range schemeFiles {
		data, err := fs.ReadFile(bundled, "payload/"+name)
		if err != nil {
			return "", err
		}
		sources[name] = data
	}
	config := filepath.Join(user, "default.custom.yaml")
	old, err := os.ReadFile(config)
	if err != nil && !os.IsNotExist(err) {
		return "", err
	}
	if !utf8.Valid(old) {
		return "", errors.New("default.custom.yaml 不是 UTF-8；未修改任何文件。")
	}
	newConfig, err := updatedConfig(strings.TrimPrefix(string(old), "\ufeff"))
	if err != nil {
		return "", err
	}
	marker := filepath.Join(user, "booru-last-backup.txt")
	previous, err := os.ReadFile(marker)
	if err != nil && !os.IsNotExist(err) {
		return "", err
	}
	var previousPath *string
	if len(previous) > 0 {
		value := strings.TrimSpace(string(previous))
		previousPath = &value
	}
	backup := filepath.Join(user, "booru-backups", fmt.Sprint(time.Now().UnixNano()))
	if err := os.MkdirAll(filepath.Dir(backup), 0755); err != nil {
		return "", err
	}
	if err := os.Mkdir(backup, 0755); err != nil {
		return "", err
	}
	m := manifest{FormatVersion: 2, UserDir: user, CreatedAt: time.Now().Format("2006-01-02 15:04:05"), PreviousManifest: previousPath}
	for _, name := range managedFiles() {
		target := filepath.Join(user, filepath.FromSlash(name))
		_, err := os.Stat(target)
		if err != nil && !os.IsNotExist(err) {
			return "", err
		}
		item := backupFile{Name: name, Existed: err == nil}
		if item.Existed {
			if err := copyFile(target, filepath.Join(backup, filepath.FromSlash(name))); err != nil {
				return "", err
			}
		}
		m.Files = append(m.Files, item)
	}
	manifestPath := filepath.Join(backup, "manifest.json")
	if err := saveManifest(manifestPath, m); err != nil {
		return "", err
	}
	for _, name := range schemeFiles {
		if err := write(filepath.Join(user, filepath.FromSlash(name)), sources[name]); err != nil {
			return "", err
		}
	}
	if err := write(config, []byte(newConfig)); err != nil {
		return "", err
	}
	for i := range m.Files {
		value, err := digest(filepath.Join(user, filepath.FromSlash(m.Files[i].Name)))
		if err != nil {
			return "", err
		}
		m.Files[i].InstalledSHA256 = value
	}
	if err := saveManifest(manifestPath, m); err != nil {
		return "", err
	}
	if err := write(marker, []byte(manifestPath)); err != nil {
		return "", err
	}
	return manifestPath, nil
}

func rollback(manifestPath string) error {
	manifestPath, err := filepath.Abs(manifestPath)
	if err != nil {
		return err
	}
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return err
	}
	var m manifest
	if err := json.Unmarshal(data, &m); err != nil {
		return err
	}
	if !filepath.IsAbs(m.UserDir) {
		return errors.New("备份中的用户目录必须是绝对路径。")
	}
	allowed := make(map[string]bool)
	for _, name := range managedFiles() {
		allowed[name] = true
	}
	// Check every managed file before restoring any of them.
	for _, item := range m.Files {
		if !allowed[item.Name] {
			return errors.New("Unexpected or duplicate file in manifest: " + item.Name)
		}
		delete(allowed, item.Name)
		target := filepath.Join(m.UserDir, filepath.FromSlash(item.Name))
		value, err := digest(target)
		if err != nil || item.InstalledSHA256 == "" || value != item.InstalledSHA256 {
			return errors.New("File changed after install; 保留现状，未执行回滚: " + target)
		}
		if item.Existed {
			if _, err := os.ReadFile(filepath.Join(filepath.Dir(manifestPath), filepath.FromSlash(item.Name))); err != nil {
				return err
			}
		}
	}
	// Pre-0.2.8 backups predate the generated annotation file.
	if m.FormatVersion < 2 {
		delete(allowed, "booru.annotations.tsv")
	}
	if len(allowed) != 0 {
		return errors.New("备份清单缺少方案文件；未执行回滚。")
	}
	for _, item := range m.Files {
		target := filepath.Join(m.UserDir, filepath.FromSlash(item.Name))
		if item.Existed {
			if err := copyFile(filepath.Join(filepath.Dir(manifestPath), filepath.FromSlash(item.Name)), target); err != nil {
				return err
			}
		} else if err := os.Remove(target); err != nil {
			return err
		}
	}
	marker := filepath.Join(m.UserDir, "booru-last-backup.txt")
	current, err := os.ReadFile(marker)
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	if strings.EqualFold(strings.TrimSpace(string(current)), manifestPath) {
		if m.PreviousManifest != nil && *m.PreviousManifest != "" {
			return write(marker, []byte(*m.PreviousManifest))
		}
		return os.Remove(marker)
	}
	return nil
}

func run(args []string) error {
	if bundleError != nil {
		return fmt.Errorf("内置资源无法读取: %w", bundleError)
	}
	flags := flag.NewFlagSet("安装绘画提示词.exe", flag.ContinueOnError)
	defaultUser := ""
	if appdata := os.Getenv("APPDATA"); appdata != "" {
		defaultUser = filepath.Join(appdata, "Rime")
	}
	user := flags.String("user-dir", defaultUser, "Rime 用户目录（默认 %APPDATA%\\Rime）")
	latest := flags.Bool("rollback-latest", false, "回滚最近一次安装；保留备份")
	backup := flags.String("rollback", "", "使用指定 manifest.json 回滚")
	showVersion := flags.Bool("version", false, "显示版本与词库类型")
	showLicense := flags.Bool("license", false, "显示项目和第三方许可")
	flags.Usage = func() {
		fmt.Fprintln(flags.Output(), "Windows 小狼毫（Rime）扩展方案独立安装器。无需 Python、.NET 或联网。\n先安装小狼毫；默认安装方案后，需在托盘菜单手动重新部署。\n用法：安装绘画提示词.exe [选项]")
		flags.PrintDefaults()
	}
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return nil
		}
		return err
	}
	if flags.NArg() > 0 {
		return errors.New("无法识别的参数；用 --help 查看用法。")
	}
	if *showVersion {
		fmt.Printf("AI Prompt IME %s / %s / windows-amd64\n", version, variant)
		return nil
	}
	if *showLicense {
		names, err := fs.ReadDir(bundled, "notices")
		if err != nil {
			return err
		}
		for _, name := range names {
			text, err := fs.ReadFile(bundled, "notices/"+name.Name())
			if err != nil {
				return err
			}
			fmt.Printf("\n--- %s ---\n%s\n", name.Name(), text)
		}
		return nil
	}
	if *latest && *backup != "" {
		return errors.New("--rollback 和 --rollback-latest 不能同时使用。")
	}
	if *latest {
		if *user == "" {
			return errors.New("无法确定 Rime 用户目录；请指定 --user-dir。")
		}
		data, err := os.ReadFile(filepath.Join(*user, "booru-last-backup.txt"))
		if err != nil {
			return err
		}
		*backup = strings.TrimSpace(string(data))
		if *backup == "" {
			return errors.New("最近备份记录为空；未修改任何文件。")
		}
	}
	if *backup != "" {
		if err := rollback(*backup); err != nil {
			return err
		}
		fmt.Println("Restored managed files. 回滚成功；请在小狼毫托盘菜单重新部署。")
		return nil
	}
	if *user == "" {
		return errors.New("无法确定 Rime 用户目录；请指定 --user-dir。")
	}
	path, err := install(*user)
	if err != nil {
		return err
	}
	fmt.Println("【安装成功】绘画提示词文件已复制到小狼毫用户文件夹。")
	kind := "默认词库"
	if variant == "searchable" {
		kind = "扩展词库"
	}
	fmt.Printf("本次安装：v%s · %s\n\n", version, kind)
	fmt.Println("【请完成最后一步，让新版本生效】")
	fmt.Println("1. 右键点击任务栏右下角的小狼毫图标，选择“重新部署”。")
	fmt.Println("2. 等待部署完成后，按 F4，选择“绘画提示词”即可使用。")
	fmt.Println("\n这是依托小狼毫运行的提示词输入方案，使用前需要已安装小狼毫。")
	fmt.Println("安装前状态已备份到：" + path)
	return nil
}

func main() {
	// UTF-8 output in the Windows console; no child processes or external runtime.
	kernel := syscall.NewLazyDLL("kernel32.dll")
	kernel.NewProc("SetConsoleOutputCP").Call(65001)
	code := 0
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "操作未完成：", err)
		code = 1
	}
	if len(os.Args) == 1 {
		if info, err := os.Stdin.Stat(); err == nil && info.Mode()&os.ModeCharDevice != 0 {
			fmt.Print("\n按 Enter 关闭窗口……")
			bufio.NewReader(os.Stdin).ReadString('\n')
		}
	}
	os.Exit(code)
}

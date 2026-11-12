package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestConfigCompatibility(t *testing.T) {
	cases := []string{
		"", "patch:\n", "patch:\n  menu/page_size: 9\n",
		"# comment\r\npatch:\r\n  schema_list:\r\n    - {schema: luna_pinyin}\r\n  menu/page_size: 9\r\n",
		"patch:\n  schema_list: # keep this\n    - {schema: luna_pinyin}\n",
		"patch:\n  schema_list:",
	}
	for _, original := range cases {
		got, err := updatedConfig(original)
		if err != nil {
			t.Fatal(err)
		}
		if strings.Count(got, "schema: booru") != 1 {
			t.Fatalf("missing/duplicate booru: %q", got)
		}
		second, err := updatedConfig(got)
		if err != nil || second != got {
			t.Fatalf("not idempotent: %q", got)
		}
		if strings.Contains(original, "luna_pinyin") && !strings.Contains(got, "luna_pinyin") {
			t.Fatal("lost original schema")
		}
		if strings.Contains(got, "\r\r\n") {
			t.Fatal("damaged CRLF")
		}
	}
	if _, err := updatedConfig("patch: {schema_list: [{schema: luna_pinyin}]}"); err == nil {
		t.Fatal("unfamiliar config accepted")
	}
}

func TestInstallAndRollback(t *testing.T) {
	user := filepath.Join(t.TempDir(), "中文 Rime")
	if err := os.Mkdir(user, 0755); err != nil {
		t.Fatal(err)
	}
	original := []byte("\xef\xbb\xbf# preserve\r\npatch:\r\n  schema_list:\r\n    - {schema: luna_pinyin}\r\n  menu/page_size: 9\r\n")
	config := filepath.Join(user, "default.custom.yaml")
	if err := os.WriteFile(config, original, 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(user, "booru.tsv"), []byte("old"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(user, "weasel.custom.yaml"), []byte("untouched"), 0644); err != nil {
		t.Fatal(err)
	}
	first, err := install(user)
	if err != nil {
		t.Fatal(err)
	}
	second, err := install(user)
	if err != nil {
		t.Fatal(err)
	}
	if err := rollback(second); err != nil {
		t.Fatal(err)
	}
	marker, err := os.ReadFile(filepath.Join(user, "booru-last-backup.txt"))
	if err != nil || string(marker) != first {
		t.Fatal("backup chain lost")
	}
	if err := rollback(first); err != nil {
		t.Fatal(err)
	}
	actual, err := os.ReadFile(config)
	if err != nil || string(actual) != string(original) {
		t.Fatal("original config not restored byte for byte")
	}
	old, err := os.ReadFile(filepath.Join(user, "booru.tsv"))
	if err != nil || string(old) != "old" {
		t.Fatal("old dictionary not restored")
	}
	untouched, _ := os.ReadFile(filepath.Join(user, "weasel.custom.yaml"))
	if string(untouched) != "untouched" {
		t.Fatal("unrelated config changed")
	}
	if _, err := os.Stat(filepath.Join(user, "booru.schema.yaml")); !os.IsNotExist(err) {
		t.Fatal("new file not removed")
	}
}

func TestRefuseConflictBeforeRollback(t *testing.T) {
	user := t.TempDir()
	path, err := install(user)
	if err != nil {
		t.Fatal(err)
	}
	config := filepath.Join(user, "default.custom.yaml")
	installed, _ := os.ReadFile(config)
	changed := filepath.Join(user, "booru.tsv")
	if err := os.WriteFile(changed, []byte("user edit"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := rollback(path); err == nil {
		t.Fatal("conflict not refused")
	}
	after, _ := os.ReadFile(config)
	if string(after) != string(installed) {
		t.Fatal("rollback partially changed config")
	}
}

func TestRefuseUnsupportedConfigBeforeWrites(t *testing.T) {
	user := t.TempDir()
	config := filepath.Join(user, "default.custom.yaml")
	original := []byte("patch: {schema_list: [{schema: luna_pinyin}]}")
	if err := os.WriteFile(config, original, 0644); err != nil {
		t.Fatal(err)
	}
	if _, err := install(user); err == nil {
		t.Fatal("unsupported syntax accepted")
	}
	entries, _ := os.ReadDir(user)
	if len(entries) != 1 {
		t.Fatal("files created before config validation")
	}
	actual, _ := os.ReadFile(config)
	if string(actual) != string(original) {
		t.Fatal("config changed")
	}
}

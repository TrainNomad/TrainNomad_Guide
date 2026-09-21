package main

import (
	"log"
	"net/http"
	"os"
	"runtime"
	"runtime/debug"
	"time"
)

func findGuidesData() (string, string) {
	// Vérifier s'il y a un repertoire resultats_guides
	if _, err := os.Stat("resultats_guides"); err == nil {
		return "resultats_guides", "directory"
	}

	if p := os.Getenv("GUIDES_PATH"); p != "" {
		return p, "binary"
	}

	for _, p := range []string{"guides.bin.gz", "guides.bin", "data/guides.bin.gz"} {
		if _, err := os.Stat(p); err == nil {
			return p, "binary"
		}
	}
	return "guides.bin.gz", "binary"
}

func main() {
	// Limiter la mémoire (Render free tier: 512 Mo)
	debug.SetMemoryLimit(256 << 20)

	path, pathType := findGuidesData()
	start := time.Now()

	var data *GuidesData
	var err error

	if pathType == "directory" {
		data, err = LoadGuidesFromDirectory(path)
	} else {
		data, err = LoadGuides(path)
	}

	if err != nil {
		log.Fatalf("chargement de %s : %v", path, err)
	}

	loadMs := time.Since(start).Milliseconds()
	runtime.GC()

	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	log.Printf("guides %s chargés en %d ms : %d guides, %d pays, heap %.1f Mo",
		path, loadMs, len(data.Guides), len(data.ByCountry), float64(m.HeapAlloc)/1e6)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}

	srv := &Server{
		data:    data,
		started: time.Now(),
		loadMs:  loadMs,
	}

	log.Printf("serveur guides sur :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, srv.routes()))
}

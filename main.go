package main

import (
	"log"
	"net/http"
	"os"
	"runtime"
	"runtime/debug"
	"time"
)

func findGuidesData() string {
	if p := os.Getenv("GUIDES_PATH"); p != "" {
		return p
	}
	for _, p := range []string{"guides.bin.gz", "guides.bin", "data/guides.bin.gz"} {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return "guides.bin.gz"
}

func main() {
	// Limiter la mémoire (Render free tier: 512 Mo)
	debug.SetMemoryLimit(256 << 20)

	path := findGuidesData()
	start := time.Now()

	data, err := LoadGuides(path)
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

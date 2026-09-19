package main

import (
	"compress/gzip"
	"encoding/json"
	"net/http"
	"runtime"
	"strings"
	"time"
)

type Server struct {
	data    *GuidesData
	started time.Time
	loadMs  int64
}

type apiError struct {
	Error  string `json:"error"`
	Detail string `json:"detail,omitempty"`
}

func (s *Server) routes() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", s.handleHealth)
	mux.HandleFunc("GET /guides", s.handleList)
	mux.HandleFunc("GET /guides/{slug}", s.handleGet)
	mux.HandleFunc("GET /countries", s.handleCountries)

	return corsMiddleware(mux)
}

func corsMiddleware(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Accept-Encoding")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		h.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, r *http.Request, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")

	// Compression gzip si supportée
	if strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
		w.Header().Set("Content-Encoding", "gzip")
		w.WriteHeader(status)
		gz := gzip.NewWriter(w)
		defer gz.Close()
		json.NewEncoder(gz).Encode(v)
		return
	}

	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, r *http.Request, status int, msg, detail string) {
	writeJSON(w, r, status, apiError{Error: msg, Detail: detail})
}

// GET /health
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	writeJSON(w, r, http.StatusOK, map[string]any{
		"status":      "ok",
		"uptime_sec":  int(time.Since(s.started).Seconds()),
		"load_ms":     s.loadMs,
		"num_guides":  len(s.data.Guides),
		"heap_mb":     float64(m.HeapAlloc) / 1e6,
		"version":     s.data.Meta.Version,
		"built_at":    s.data.Meta.BuiltAt,
	})
}

// GET /guides?country=France&featured=true&search=paris
func (s *Server) handleList(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	country := query.Get("country")
	search := strings.ToLower(query.Get("search"))
	featuredOnly := query.Get("featured") == "true"

	var result []GuideIndex

	if country != "" {
		result = s.data.GetByCountry(country)
	} else {
		result = s.data.GetIndex()
	}

	// Filtrage
	if search != "" || featuredOnly {
		filtered := make([]GuideIndex, 0)
		for _, g := range result {
			if featuredOnly && !g.Featured {
				continue
			}
			if search != "" {
				if !strings.Contains(strings.ToLower(g.Name), search) &&
					!strings.Contains(strings.ToLower(g.Country), search) &&
					!strings.Contains(strings.ToLower(g.Description), search) {
					continue
				}
			}
			filtered = append(filtered, g)
		}
		result = filtered
	}

	writeJSON(w, r, http.StatusOK, map[string]any{
		"guides": result,
		"total":  len(result),
	})
}

// GET /guides/{slug}
func (s *Server) handleGet(w http.ResponseWriter, r *http.Request) {
	slug := r.PathValue("slug")
	if slug == "" {
		writeError(w, r, http.StatusBadRequest, "slug manquant", "")
		return
	}

	guide := s.data.GetGuide(slug)
	if guide == nil {
		writeError(w, r, http.StatusNotFound, "guide non trouvé", "Aucun guide avec le slug: "+slug)
		return
	}

	writeJSON(w, r, http.StatusOK, guide)
}

// GET /countries
func (s *Server) handleCountries(w http.ResponseWriter, r *http.Request) {
	countries := s.data.Countries()

	// Compter les guides par pays
	countByCountry := make(map[string]int)
	for _, c := range countries {
		countByCountry[c] = len(s.data.ByCountry[c])
	}

	writeJSON(w, r, http.StatusOK, map[string]any{
		"countries": countries,
		"counts":    countByCountry,
	})
}

package main

import (
	"bytes"
	"compress/gzip"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
)

// Guide représente un guide de destination complet
type Guide struct {
	Slug             string    `json:"slug"`
	Name             string    `json:"name"`
	Country          string    `json:"country"`
	CountryCode      string    `json:"country_code"`
	Image            string    `json:"image"`
	HeroImage        string    `json:"hero_image"`
	Description      string    `json:"description"`
	ReadingTime      int       `json:"reading_time"`
	Featured         bool      `json:"featured"`
	FeaturedTitle    string    `json:"featured_title,omitempty"`
	FeaturedSubtitle string    `json:"featured_subtitle,omitempty"`
	Sections         []Section `json:"sections"`
	QuickFacts       []Fact    `json:"quick_facts"`
	Tags             []string  `json:"tags"`
}

// Section représente une section du guide (gare, coworking, quartiers, etc.)
type Section struct {
	ID      string `json:"id"`
	Title   string `json:"title"`
	Icon    string `json:"icon"`
	Content string `json:"content"`
}

// Fact représente un fait rapide (durée, wifi, coût, climat)
type Fact struct {
	Icon  string `json:"icon"`
	Label string `json:"label"`
	Value string `json:"value"`
}

// GuideIndex représente un guide dans la liste (version légère)
type GuideIndex struct {
	Slug             string   `json:"slug"`
	Name             string   `json:"name"`
	Country          string   `json:"country"`
	CountryCode      string   `json:"country_code"`
	Image            string   `json:"image"`
	Description      string   `json:"description"`
	ReadingTime      int      `json:"reading_time"`
	Featured         bool     `json:"featured"`
	FeaturedTitle    string   `json:"featured_title,omitempty"`
	FeaturedSubtitle string   `json:"featured_subtitle,omitempty"`
	Tags             []string `json:"tags"`
}

// Meta contient les métadonnées du fichier binaire
type Meta struct {
	Version   int    `json:"version"`
	BuiltAt   string `json:"built_at"`
	NumGuides int    `json:"num_guides"`
}

// GuidesData contient toutes les données des guides chargées en RAM
type GuidesData struct {
	Meta    Meta
	Guides  []Guide
	Index   map[string]int // slug -> index dans Guides
	ByCountry map[string][]int // country -> indices
}

// section helper pour le parsing binaire
type binSection struct {
	dtype byte
	count uint64
	data  []byte
}

// LoadGuides charge les données depuis le fichier binaire compressé
func LoadGuides(path string) (*GuidesData, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var r io.Reader = f
	if strings.HasSuffix(path, ".gz") {
		gz, err := gzip.NewReader(f)
		if err != nil {
			return nil, err
		}
		defer gz.Close()
		r = gz
	}

	raw, err := io.ReadAll(r)
	if err != nil {
		return nil, err
	}

	return parseGuides(raw)
}

func parseGuides(raw []byte) (*GuidesData, error) {
	// Format: TNGDE001 + nsections (4 bytes) + padding (4 bytes)
	if len(raw) < 16 || !bytes.Equal(raw[:8], []byte("TNGDE001")) {
		return nil, fmt.Errorf("format guides.bin inconnu")
	}

	le := binary.LittleEndian
	nsec := int(le.Uint32(raw[8:12]))
	pos := 16

	secs := make(map[string]binSection, nsec)
	for i := 0; i < nsec; i++ {
		if pos+48 > len(raw) {
			return nil, fmt.Errorf("guides.bin tronqué")
		}
		name := string(bytes.TrimRight(raw[pos:pos+24], "\x00"))
		dtype := raw[pos+24]
		count := le.Uint64(raw[pos+32 : pos+40])
		size := int(le.Uint64(raw[pos+40 : pos+48]))
		pos += 48
		if pos+size > len(raw) {
			return nil, fmt.Errorf("section %s tronquée", name)
		}
		secs[name] = binSection{dtype, count, raw[pos : pos+size]}
		pos += size + (8-size%8)%8
	}

	// Récupérer les données
	var perr error
	get := func(name string, dtype byte) []byte {
		s, ok := secs[name]
		if !ok {
			if perr == nil {
				perr = fmt.Errorf("section manquante : %s", name)
			}
			return nil
		}
		if s.dtype != dtype && perr == nil {
			perr = fmt.Errorf("section %s : type %d attendu, %d trouvé", name, dtype, s.dtype)
		}
		return s.data
	}

	d := &GuidesData{
		Index:     make(map[string]int),
		ByCountry: make(map[string][]int),
	}

	// Parse meta
	if err := json.Unmarshal(get("meta", 1), &d.Meta); err != nil {
		return nil, fmt.Errorf("meta : %w", err)
	}

	// Parse guides (stockés en JSON pour simplicité)
	guidesJSON := get("guides", 1)
	if err := json.Unmarshal(guidesJSON, &d.Guides); err != nil {
		return nil, fmt.Errorf("guides : %w", err)
	}

	if perr != nil {
		return nil, perr
	}

	// Construire les index
	for i, g := range d.Guides {
		d.Index[g.Slug] = i
		d.ByCountry[g.Country] = append(d.ByCountry[g.Country], i)
	}

	return d, nil
}

// GetGuide retourne un guide par son slug
func (d *GuidesData) GetGuide(slug string) *Guide {
	if idx, ok := d.Index[slug]; ok {
		return &d.Guides[idx]
	}
	return nil
}

// GetIndex retourne la liste des guides (version légère)
func (d *GuidesData) GetIndex() []GuideIndex {
	result := make([]GuideIndex, len(d.Guides))
	for i, g := range d.Guides {
		result[i] = GuideIndex{
			Slug:             g.Slug,
			Name:             g.Name,
			Country:          g.Country,
			CountryCode:      g.CountryCode,
			Image:            g.Image,
			Description:      g.Description,
			ReadingTime:      g.ReadingTime,
			Featured:         g.Featured,
			FeaturedTitle:    g.FeaturedTitle,
			FeaturedSubtitle: g.FeaturedSubtitle,
			Tags:             g.Tags,
		}
	}
	return result
}

// GetByCountry retourne les guides d'un pays
func (d *GuidesData) GetByCountry(country string) []GuideIndex {
	indices, ok := d.ByCountry[country]
	if !ok {
		return nil
	}
	result := make([]GuideIndex, len(indices))
	for i, idx := range indices {
		g := d.Guides[idx]
		result[i] = GuideIndex{
			Slug:             g.Slug,
			Name:             g.Name,
			Country:          g.Country,
			CountryCode:      g.CountryCode,
			Image:            g.Image,
			Description:      g.Description,
			ReadingTime:      g.ReadingTime,
			Featured:         g.Featured,
			FeaturedTitle:    g.FeaturedTitle,
			FeaturedSubtitle: g.FeaturedSubtitle,
			Tags:             g.Tags,
		}
	}
	return result
}

// Countries retourne la liste des pays disponibles
func (d *GuidesData) Countries() []string {
	countries := make([]string, 0, len(d.ByCountry))
	for c := range d.ByCountry {
		countries = append(countries, c)
	}
	return countries
}

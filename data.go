package main

import (
	"bytes"
	"compress/gzip"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// EssentialItem represente un element essentiel (a voir, experience, mobilite)
type EssentialItem struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

// Essentials represente la section "L'essentiel"
type Essentials struct {
	ToSee       []EssentialItem `json:"to_see,omitempty"`
	Experiences []EssentialItem `json:"experiences,omitempty"`
	Mobility    []EssentialItem `json:"mobility,omitempty"`
}

// ItineraryStep represente une etape de l'itineraire
type ItineraryStep struct {
	Time        string `json:"time"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Type        string `json:"type"` // transport, visit, food, leisure
}

// ItineraryDay represente une journee de l'itineraire
type ItineraryDay struct {
	Day         int             `json:"day"`
	Title       string          `json:"title"`
	Description string          `json:"description"`
	Steps       []ItineraryStep `json:"steps"`
}

// TrainStation represente une gare
type TrainStation struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Services    []string `json:"services,omitempty"`
	Connections []string `json:"connections,omitempty"`
}

// TrainRoute represente une liaison ferroviaire
type TrainRoute struct {
	From        string   `json:"from"`
	Description string   `json:"description"`
	Duration    string   `json:"duration"`
	Operators   []string `json:"operators,omitempty"`
}

// TrainTravel represente la section voyage en train
type TrainTravel struct {
	Intro    string         `json:"intro,omitempty"`
	Stations []TrainStation `json:"stations,omitempty"`
	Routes   []TrainRoute   `json:"routes,omitempty"`
}

// PracticalInfo represente un conseil pratique
type PracticalInfo struct {
	Title   string `json:"title"`
	Icon    string `json:"icon"`
	Content string `json:"content"`
}

// JourneyPoint represente un point du trajet
type JourneyPoint struct {
	Name string  `json:"name"`
	Code string  `json:"code,omitempty"`
	Lat  float64 `json:"lat"`
	Lon  float64 `json:"lon"`
}

// JourneyLeg represente une etape du trajet (train ou correspondance)
type JourneyLeg struct {
	ID          int          `json:"id"`
	Type        string       `json:"type"` // train, transfer
	Operator    string       `json:"operator,omitempty"`
	TrainType   string       `json:"train_type,omitempty"`
	TrainNumber string       `json:"train_number,omitempty"`
	From        JourneyPoint `json:"from"`
	To          JourneyPoint `json:"to,omitempty"`
	Departure   string       `json:"departure,omitempty"`
	Arrival     string       `json:"arrival,omitempty"`
	DurationMin int          `json:"duration_min"`
	Mode        string       `json:"mode,omitempty"` // walk, wait
	Description string       `json:"description,omitempty"`
	Overnight   bool         `json:"overnight,omitempty"`
	Amenities   []string     `json:"amenities,omitempty"`
}

// DefaultJourney represente le trajet de reference
type DefaultJourney struct {
	Origin      JourneyPoint `json:"origin"`
	Destination JourneyPoint `json:"destination"`
	Legs        []JourneyLeg `json:"legs"`
}

// PhotoSpot represente un spot photo le long du trajet
type PhotoSpot struct {
	Name        string  `json:"name"`
	Description string  `json:"description"`
	KmFromParis int     `json:"km_from_paris"`
	Lat         float64 `json:"lat"`
	Lon         float64 `json:"lon"`
	BestSide    string  `json:"best_side"`
	Type        string  `json:"type"` // coastal, mountain, bridge, urban
}

// Guide represente un guide de destination complet
type Guide struct {
	Slug             string          `json:"slug"`
	Name             string          `json:"name"`
	Country          string          `json:"country"`
	CountryCode      string          `json:"country_code"`
	Image            string          `json:"image"`
	HeroImage        string          `json:"hero_image"`
	Description      string          `json:"description"`
	ReadingTime      int             `json:"reading_time"`
	Featured         bool            `json:"featured"`
	FeaturedTitle    string          `json:"featured_title,omitempty"`
	FeaturedSubtitle string          `json:"featured_subtitle,omitempty"`
	Sections         []Section       `json:"sections"`
	QuickFacts       []Fact          `json:"quick_facts"`
	Tags             []string        `json:"tags"`
	Introduction     string          `json:"introduction,omitempty"`
	Essentials       *Essentials     `json:"essentials,omitempty"`
	Itinerary        []ItineraryDay  `json:"itinerary,omitempty"`
	TrainTravel      *TrainTravel    `json:"train_travel,omitempty"`
	Practical        []PracticalInfo `json:"practical,omitempty"`
	DefaultJourney   *DefaultJourney `json:"default_journey,omitempty"`
	PhotoSpots       []PhotoSpot     `json:"photo_spots,omitempty"`
}

// Section represente une section du guide (gare, coworking, quartiers, etc.)
type Section struct {
	ID      string `json:"id"`
	Title   string `json:"title"`
	Icon    string `json:"icon"`
	Content string `json:"content"`
}

// Fact represente un fait rapide (duree, wifi, cout, climat)
type Fact struct {
	Icon  string `json:"icon"`
	Label string `json:"label"`
	Value string `json:"value"`
}

// GuideIndex represente un guide dans la liste (version legere)
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

// Meta contient les metadonnees du fichier binaire
type Meta struct {
	Version   int    `json:"version"`
	BuiltAt   string `json:"built_at"`
	NumGuides int    `json:"num_guides"`
}

// GuidesData contient toutes les donnees des guides chargees en RAM
type GuidesData struct {
	Meta      Meta
	Guides    []Guide
	Index     map[string]int   // slug -> index dans Guides
	ByCountry map[string][]int // country -> indices
}

// section helper pour le parsing binaire
type binSection struct {
	dtype byte
	count uint64
	data  []byte
}

// LoadGuidesFromDirectory charge les donnees depuis les fichiers JSON individuels
func LoadGuidesFromDirectory(dirPath string) (*GuidesData, error) {
	d := &GuidesData{
		Index:     make(map[string]int),
		ByCountry: make(map[string][]int),
	}

	d.Meta.Version = 1
	d.Meta.BuiltAt = "dynamic"

	// Parcourir les dossiers de pays
	countriesDirs, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, fmt.Errorf("impossible de lire le repertoire %s: %w", dirPath, err)
	}

	for _, countryEntry := range countriesDirs {
		if !countryEntry.IsDir() || countryEntry.Name() == "index.json" {
			continue
		}

		countryPath := filepath.Join(dirPath, countryEntry.Name())
		countryName := countryEntry.Name()

		// Parcourir les fichiers JSON du pays
		files, err := os.ReadDir(countryPath)
		if err != nil {
			continue
		}

		for _, file := range files {
			if file.IsDir() || !strings.HasSuffix(file.Name(), ".json") {
				continue
			}

			filePath := filepath.Join(countryPath, file.Name())

			// Lire et parser le fichier JSON
			jsonData, err := os.ReadFile(filePath)
			if err != nil {
				continue
			}

			var guide Guide
			if err := json.Unmarshal(jsonData, &guide); err != nil {
				continue
			}

			// Ajouter le guide
			idx := len(d.Guides)
			d.Guides = append(d.Guides, guide)
			d.Index[guide.Slug] = idx
			d.ByCountry[countryName] = append(d.ByCountry[countryName], idx)
		}
	}

	d.Meta.NumGuides = len(d.Guides)

	if d.Meta.NumGuides == 0 {
		return nil, fmt.Errorf("aucun guide trouve dans %s", dirPath)
	}

	return d, nil
}

// LoadGuides charge les donnees depuis le fichier binaire compresse
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
			return nil, fmt.Errorf("guides.bin tronque")
		}
		name := string(bytes.TrimRight(raw[pos:pos+24], "\x00"))
		dtype := raw[pos+24]
		count := le.Uint64(raw[pos+32 : pos+40])
		size := int(le.Uint64(raw[pos+40 : pos+48]))
		pos += 48
		if pos+size > len(raw) {
			return nil, fmt.Errorf("section %s tronquee", name)
		}
		secs[name] = binSection{dtype, count, raw[pos : pos+size]}
		pos += size + (8-size%8)%8
	}

	// Recuperer les donnees
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
			perr = fmt.Errorf("section %s : type %d attendu, %d trouve", name, dtype, s.dtype)
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

	// Parse guides (stockes en JSON pour simplicite)
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

// GetIndex retourne la liste des guides (version legere)
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

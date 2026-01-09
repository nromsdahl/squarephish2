package email

import (
        "bytes"
        "crypto/tls"
        "fmt"
        "net/smtp"
        "strings"

        "github.com/jordan-wright/email"
        "github.com/nromsdahl/squarephish2/internal/models"
        log "github.com/sirupsen/logrus"
)

// loginAuth implements LOGIN authentication for SMTP
type loginAuth struct {
    username, password string
}

// LoginAuth returns an Auth that implements the LOGIN authentication mechanism
func LoginAuth(username, password string) smtp.Auth {
    return &loginAuth{username, password}
}

func (a *loginAuth) Start(server *smtp.ServerInfo) (string, []byte, error) {
    return "LOGIN", []byte{}, nil
}

func (a *loginAuth) Next(fromServer []byte, more bool) ([]byte, error) {
    if more {
        switch string(fromServer) {
        case "Username:", "User Name":
            return []byte(a.username), nil
        case "Password:":
            return []byte(a.password), nil
        default:
            return []byte(a.username), nil
        }
    }
    return nil, nil
}

// SendQREmail sends an email containing a QR code using the provided SMTP configuration
// and message details.
// Parameters:
//   - config:      SMTP server configuration (host, port, username, password).
//   - sender:      The "From" address for the email header (should usually match config.Username).
//   - recipients:  A slice of email addresses to send the email to.
//   - subject:     The subject line of the email.
//   - body:        The plain text body of the email.
//   - qr:          The QR code image as bytes.
//
// It returns an error if authentication or sending fails.

func SendQREmail(config models.SMTPConfig,
                     sender string, recipients []string,
                     subject, body string, qr []byte) error {
        var err error

        if len(recipients) == 0 {
                return fmt.Errorf("no recipients provided")
        }

        // Construct the SMTP server address string.
        smtpServerAddr := config.Host + ":" + config.Port

        // Set up SMTP authentication information.
        auth := LoginAuth(config.Username, config.Password)

        e := email.NewEmail()
        e.From = sender
        e.To = recipients
        e.Subject = subject
        e.HTML = []byte(body)

        var a *email.Attachment
        a, err = e.Attach(bytes.NewReader(qr), "qrcode", "image/png")
        if err != nil {
                return fmt.Errorf("failed to attach inline QR code: %w", err)
        }
        a.HTMLRelated = true

        // Use TLS if required by the server
        if config.Port == "465" {
                err = e.SendWithTLS(smtpServerAddr, auth, &tls.Config{
                        InsecureSkipVerify: true,
                        ServerName:         config.Host,
                })
        } else if config.Port == "587" {
                err = e.SendWithStartTLS(smtpServerAddr, auth, &tls.Config{
                        InsecureSkipVerify: true,
                        ServerName:         config.Host,
                })
        } else {
                err = e.Send(smtpServerAddr, auth)
        }

        if err != nil {
                return fmt.Errorf("failed to send email: %w", err)
        }

        log.Printf("Email sent to victim(s): %s\n", strings.Join(recipients, ", "))
        return nil
}

// SendEmail sends an email using the provided SMTP configuration and message details.
// Parameters:
//   - config:      SMTP server configuration (host, port, username, password).
//   - sender:      The "From" address for the email header (should usually match config.Username).
//   - recipients:  A slice of email addresses to send the email to.
//   - subject:     The subject line of the email.
//   - body:        The plain text body of the email.
//
// It returns an error if authentication or sending fails.
func SendEmail(config models.SMTPConfig,
                   sender string, recipients []string,
                   subject, body string) error {
        var err error

        if len(recipients) == 0 {
                return fmt.Errorf("no recipients provided")
        }

        // Construct the SMTP server address string.
        smtpServerAddr := config.Host + ":" + config.Port

        // Set up SMTP authentication information.
        auth := LoginAuth(config.Username, config.Password)

        e := email.NewEmail()
        e.From = sender
        e.To = recipients
        e.Subject = subject
        e.HTML = []byte(body)

        // Use TLS if required by the server
        if config.Port == "465" {
                err = e.SendWithTLS(smtpServerAddr, auth, &tls.Config{
                        InsecureSkipVerify: true,
                        ServerName:         config.Host,
                })
        } else if config.Port == "587" {
                err = e.SendWithStartTLS(smtpServerAddr, auth, &tls.Config{
                        InsecureSkipVerify: true,
                        ServerName:         config.Host,
                })
        } else {
                err = e.Send(smtpServerAddr, auth)
        }

        if err != nil {
                return fmt.Errorf("failed to send email: %w", err)
        }

        log.Printf("Email sent to victim(s): %s\n", strings.Join(recipients, ", "))
        return nil
}

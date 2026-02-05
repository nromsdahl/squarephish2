package server

// ------------------------------------------------------------------------
// https://github.com/denniskniep/DeviceCodePhishing
// https://github.com/denniskniep/DeviceCodePhishing/blob/main/LICENSE
//
// Copyright 2026 Dennis Kniep
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
	"encoding/json"
	"errors"
	"net/http"
	"net/url"
	"strings"

	"github.com/nromsdahl/squarephish2/internal/models"
)

// getUserRealmInfo retrieves the Microsoft realm information based on a
// given UPN.
// Parameters:
//   - upn: Random username + target domain.
//
// It returns the Microsoft realm for the given domain in the UPN or an
// error if the tenant doesn't exist or fails to retrieve.
func getUserRealmInfo(upn string) (*models.UserRealmInfo, error) {
	resp, err := http.Get("https://login.microsoftonline.com/common/userrealm/" + upn + "?api-version=2.1")

	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		errMsg := "Request failed with status code:" + resp.Status
		return nil, errors.New(errMsg)
	}

	var userRealmInfo models.UserRealmInfo
	err = json.NewDecoder(resp.Body).Decode(&userRealmInfo)

	if err != nil {
		return nil, err
	}

	return &userRealmInfo, nil
}

// getOidcInfo retrieves the Microsoft OpenID Configuration based on a
// given domain.
// Parameters:
//   - domain: The tenant domain name.
//
// It returns the Microsoft OpenID Configuration for the given domain
// in the UPN or an error if the tenant doesn't exist or fails to
// retrieve.
func getOidcInfo(domain string) (*models.OidcInfo, error) {
	resp, err := http.Get("https://login.microsoftonline.com/" + domain + "/.well-known/openid-configuration")

	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		errMsg := "Request failed with status code:" + resp.Status
		return nil, errors.New(errMsg)
	}

	var oidcInfo models.OidcInfo
	err = json.NewDecoder(resp.Body).Decode(&oidcInfo)

	if err != nil {
		return nil, err
	}

	return &oidcInfo, nil
}

// GetTenantInfo queries the tenant information from Microsoft based on a
// given domain.
// Parameters:
//   - domain: The tenant domain name.
//
// It returns the tenant information or an error if the tenant doesn't exist
// or fails to retrieve.
func GetTenantInfo(domain string) (*models.TenantInfo, error) {
	upn := "CUSTOM_USERNAME@" + domain // TODO: Fix username randomization

	userRealmInfo, err := getUserRealmInfo(upn)
	if err != nil {
		return nil, err
	}

	if !strings.EqualFold(domain, userRealmInfo.DomainName) {
		errMsg := "Specified Domain " + domain + "does not match with retrieved DomainName " + userRealmInfo.DomainName
		return nil, errors.New(errMsg)
	}

	oidcInfo, err := getOidcInfo(domain)
	if err != nil {
		return nil, err
	}

	issuerUrl, err := url.Parse(oidcInfo.Issuer)
	if err != nil {
		return nil, err
	}
	tenantId := strings.Replace(issuerUrl.Path, "/", "", -1)

	federatedAuthUrl, err := url.Parse(userRealmInfo.FederatedAuthURL)
	if err != nil {
		return nil, err
	}
	userRealmInfo.ParsedFederatedAuthURL = federatedAuthUrl

	return &models.TenantInfo{
		Domain:        domain,
		TenantId:      tenantId,
		ExampleUpn:    upn,
		UserRealmInfo: userRealmInfo,
		OidcInfo:      oidcInfo,
	}, nil
}

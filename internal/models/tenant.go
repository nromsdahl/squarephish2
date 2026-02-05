package models

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
	"net/url"
)

// TenantInfo represents the Microsoft Tenant information.
type TenantInfo struct {
	Domain        string
	TenantId      string
	ExampleUpn    string
	UserRealmInfo *UserRealmInfo
	OidcInfo      *OidcInfo
}

// UserRealmInfo represents the Microsoft Realm information.
type UserRealmInfo struct {
	NameSpaceType          string `json:"NameSpaceType"`
	Login                  string `json:"Login"`
	DomainName             string `json:"DomainName"`
	FederationBrandName    string `json:"FederationBrandName"`
	FederationProtocol     string `json:"federation_protocol"`
	FederatedAuthURL       string `json:"AuthURL"`
	ParsedFederatedAuthURL *url.URL
}

// UserRealmInfo represents the Microsoft OpenID Configuration.
type OidcInfo struct {
	Issuer string `json:"issuer"`
}

// GetFederatedAuthURLHost returns the host of the federated authentication URL.
// Parameters:
//   - r: The UserRealmInfo object.
//
// It returns the host of the federated authentication URL.
func (r *UserRealmInfo) GetFederatedAuthURLHost() string {
	return r.ParsedFederatedAuthURL.Host
}

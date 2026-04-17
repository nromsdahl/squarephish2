from dataclasses import dataclass, field


@dataclass
class SMTPConfig:
    host: str = ""
    port: str = ""
    username: str = ""
    password: str = ""


@dataclass
class SquarePhishConfig:
    host: str = ""
    port: str = ""


@dataclass
class EmailConfig:
    sender: str = ""
    subject: str = ""
    body: str = ""


@dataclass
class EntraConfig:
    client_id: str = ""
    scope: str = ""
    tenant: str = ""
    auto_prt: str = ""


@dataclass
class RequestConfig:
    user_agent: str = ""


@dataclass
class TokenResponse:
    token_type: str = ""
    scope: str = ""
    expires_in: int = 0
    ext_expires_in: int = 0
    access_token: str = ""
    refresh_token: str = ""
    id_token: str = ""


@dataclass
class Credential:
    email: str = ""
    token: TokenResponse = field(default_factory=TokenResponse)


@dataclass
class DeviceCodeResponse:
    user_code: str = ""
    device_code: str = ""
    verification_uri: str = ""
    expires_in: int = 0
    interval: int = 0
    message: str = ""


@dataclass
class PRTResult:
    email: str = ""
    prt: str = ""
    session_key: str = ""


@dataclass
class PendingTokenResponse:
    error: str = ""
    error_description: str = ""
    error_codes: list = field(default_factory=list)
    timestamp: str = ""
    trace_id: str = ""
    correlation_id: str = ""


@dataclass
class DashboardData:
    emails_sent: int = 0
    emails_scanned: int = 0
    credentials: list = field(default_factory=list)
    prt_results: list = field(default_factory=list)
    active_page: str = ""
    title: str = ""


@dataclass
class ConfigData:
    smtp_config: SMTPConfig = field(default_factory=SMTPConfig)
    squarephish_config: SquarePhishConfig = field(default_factory=SquarePhishConfig)
    email_config: EmailConfig = field(default_factory=EmailConfig)
    entra_config: EntraConfig = field(default_factory=EntraConfig)
    request_config: RequestConfig = field(default_factory=RequestConfig)
    active_page: str = ""
    title: str = ""


@dataclass
class EmailData:
    active_page: str = ""
    title: str = ""

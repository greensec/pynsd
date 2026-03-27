import enum


class NSDCommand(enum.Enum):
    """Enumeration of all NSD control commands."""

    # Server control commands
    STOP = "stop"
    RELOAD = "reload"
    RECONFIG = "reconfig"
    REPATTERN = "repattern"
    LOG_REOPEN = "log_reopen"

    # Zone management commands
    ADD_ZONE = "addzone"
    DEL_ZONE = "delzone"
    CHANGE_ZONE = "changezone"
    ADD_ZONES = "addzones"
    DEL_ZONES = "delzones"
    WRITE = "write"
    NOTIFY = "notify"
    TRANSFER = "transfer"
    FORCE_TRANSFER = "force_transfer"
    ZONE_STATUS = "zonestatus"

    # Server information
    STATUS = "status"
    STATS = "stats"
    STATS_NO_RESET = "stats_noreset"
    SERVER_PID = "serverpid"

    # TSIG key management
    PRINT_TSIG = "print_tsig"
    UPDATE_TSIG = "update_tsig"
    ADD_TSIG = "add_tsig"
    DEL_TSIG = "del_tsig"
    ASSOC_TSIG = "assoc_tsig"

    # Cookie secrets
    ADD_COOKIE_SECRET = "add_cookie_secret"
    DROP_COOKIE_SECRET = "drop_cookie_secret"
    ACTIVATE_COOKIE_SECRET = "activate_cookie_secret"
    PRINT_COOKIE_SECRETS = "print_cookie_secrets"

    # Verbosity control
    VERBOSITY = "verbosity"

    def __str__(self) -> str:
        return self.value

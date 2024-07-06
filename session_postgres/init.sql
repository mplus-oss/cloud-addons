CREATE TABLE sessions (
    key CHAR(40) PRIMARY KEY,
    context JSONB NOT NULL,
    db VARCHAR(64) NOT NULL,
    debug VARCHAR(20) NOT NULL,
    uid INT,
    session_token CHAR(64),
    expired_at TIMESTAMP NOT NULL
);
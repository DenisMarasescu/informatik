from enum import Enum


class TokenKind(Enum):
    SOF = "<SOF>"
    EOF = "<EOF>"
    BRACE_L = "{"
    BRACE_R = "}"
    BRACKET_L = "["
    BRACKET_R = "]"
    IDENTIFIER = "Identifier"
    DESCRIPTION = "Description"
    NEWLINE = "Newline"

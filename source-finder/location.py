# SPDX-License-Identifier: Apache-2.0

class SourceLocation:
    def __init__(self, connection: str, tag: str | None):
        self.connection = connection
        self.tag = tag
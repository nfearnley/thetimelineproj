# Copyright (C) 2009, 2010, 2011  Rickard Lindberg, Roger Lindberg
#
# This file is part of Timeline.
#
# Timeline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Timeline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Timeline.  If not, see <http://www.gnu.org/licenses/>.


import autopilotlib.manuscript.scanner as scanner


class Instruction():
    """
    The base class for all types of instructions.
    
    An instruction always belongs to a Manuscript.
    
    Textual syntax:  <instruction-name> <instruction-target>  <optional-arglist>

    """
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.include = False
        self.comment = False
        self.start = False
        
    def __str__(self):
        text = []
        for token in self.tokens:
            if token.id in (scanner.KEYWORD, ):
                text.append(" ")
            text.append(token.lexeme)
        return "".join(text).strip()

    def arg(self, index):
        token = self.tokens[index]
        if token.id == scanner.STRING:
            return token.lexeme[1:-1]
        else:
            return token.lexeme

    def get_all_args(self):
        args = []
        for token in self.tokens:
            if token.id == scanner.ID:
                args.append(token.lexeme)
            elif token.id == scanner.STRING:
                args.append(token.lexeme[1:-1])
        return args
            
    def execute(self, manuscript, win=None):
        manuscript.execute_next_instruction()

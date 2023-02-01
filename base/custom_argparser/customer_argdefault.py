"""overwrites some argparse defaults methods.
mainly for formatting.

Author Mus spyroot@gmail.com
"""
import argparse
import textwrap as _textwrap


class CustomArgumentDefaultsHelpFormatter(argparse.HelpFormatter):
    """Help message formatter which adds default values to argument help.
    Only the name of this class is considered a public API. All the methods
    provided by the class are considered an implementation detail.
    """

    def _get_help_string(self, action):
        help_msg = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help_msg += ' (default: %(default)s)'
        return help_msg

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
            # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)

    def _iter_indented_subactions(self, action):
        """Sort and ident command
        :param action:
        :return:
        """
        try:
            get_subactions = action._get_subactions
        except AttributeError:
            pass
        else:
            self._indent()
            if isinstance(action, argparse._SubParsersAction):
                for subaction in sorted(get_subactions(), key=lambda x: x.dest):
                    yield subaction
            else:
                for subaction in get_subactions():
                    yield subaction
            self._dedent()

    def _fill_text(self, text, width, indent):
        """
        :param text:
        :param width:
        :param indent:
        :return:
        """
        text = self._whitespace_matcher.sub(' ', text).strip()
        paragraphs = text.split('|n ')
        multiline_text = ''
        for paragraph in paragraphs:
            formatted_paragraph = _textwrap.fill(paragraph, width,
                                                 initial_indent=indent,
                                                 subsequent_indent=indent) + '\n'
            multiline_text = multiline_text + formatted_paragraph
        return multiline_text

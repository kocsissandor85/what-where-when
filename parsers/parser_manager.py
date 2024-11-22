import importlib
import pkgutil
from parsers.base_parser import BaseParser


class ParserManager:
    def __init__(self):
        self.parsers = {}

    def register_parser(self, name, parser_instance):
        """Register a parser with a unique name."""
        if not isinstance(parser_instance, BaseParser):
            raise ValueError(f"Parser {name} must inherit from BaseParser.")
        self.parsers[name] = parser_instance

    def auto_register_parsers(self, package="parsers"):
        """Dynamically register all parsers in the package."""
        for _, module_name, _ in pkgutil.iter_modules([package]):
            if module_name not in ["base_parser", "parser_manager", "__init__"]:
                module = importlib.import_module(f"{package}.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseParser) and attr is not BaseParser:
                        self.register_parser(module_name, attr())
                        print(f"Registered parser: {module_name}")

    def get_parser(self, name):
        """Retrieve a parser by its name."""
        return self.parsers.get(name, None)

    def run_all_parsers(self):
        """Run all registered parsers and return a combined list of events."""
        all_events = []
        for name, parser in self.parsers.items():
            print(f"Running parser: {name}")
            events = parser.fetch_data()
            all_events.extend(events)
        return all_events

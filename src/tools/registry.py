# Tool module mapping with lazy imports
TOOL_MODULES = {
    "core_stock_apis": "src.tools.core_stock_apis",
    "options_data_apis": "src.tools.options_data_apis",
    "alpha_intelligence": "src.tools.alpha_intelligence",
    "commodities": "src.tools.commodities",
    "cryptocurrencies": "src.tools.cryptocurrencies",
    "economic_indicators": "src.tools.economic_indicators",
    "forex": "src.tools.forex",
    "fundamental_data": "src.tools.fundamental_data",
    "technical_indicators": [
        "src.tools.technical_indicators_part1",
        "src.tools.technical_indicators_part2", 
        "src.tools.technical_indicators_part3",
        "src.tools.technical_indicators_part4"
    ],
    "ping": "src.tools.ping"
}

# Registry for decorated tools by category
_tool_registries = {}
_all_tools_registry = []

def tool(func):
    """Decorator to mark functions as MCP tools"""
    # Determine which module/category this function belongs to
    module_name = func.__module__.split('.')[-1]  # Get last part of module name
    
    if module_name not in _tool_registries:
        _tool_registries[module_name] = []
    
    _tool_registries[module_name].append(func)
    _all_tools_registry.append(func)
    return func

def register_all_tools(mcp):
    """Register all decorated tools"""
    # Import all modules to trigger decoration
    import importlib
    for module_spec in TOOL_MODULES.values():
        if isinstance(module_spec, list):
            for module_name in module_spec:
                importlib.import_module(module_name)
        else:
            importlib.import_module(module_spec)
    
    # Register all decorated tools
    for func in _all_tools_registry:
        mcp.tool()(func)

def register_tools_by_categories(mcp, categories):
    """Register tools from multiple categories"""
    if not categories:
        register_all_tools(mcp)
        return
    
    # Validate all categories first
    invalid_categories = [cat for cat in categories if cat not in TOOL_MODULES]
    if invalid_categories:
        raise ValueError(f"Unknown tool categories: {', '.join(invalid_categories)}")
    
    # Import specified category modules to trigger decoration
    import importlib
    for category in categories:
        if category in TOOL_MODULES:
            module_spec = TOOL_MODULES[category]
            if isinstance(module_spec, list):
                for module_name in module_spec:
                    importlib.import_module(module_name)
            else:
                importlib.import_module(module_spec)
    
    # Register tools from specified categories
    for category in categories:
        if category in _tool_registries:
            for func in _tool_registries[category]:
                mcp.tool()(func)
def dropdown(
        layout,
        config,
        attribute: str,
        text: str,
        icon: str = None,
        icon_value: str = None,
        result: dict = None
) -> bool:
    row = layout.row(align=True)
    if row.prop(
            config,
            attribute,
            icon='TRIA_DOWN' if getattr(config, attribute) else 'TRIA_RIGHT',
            text=text,
            emboss=False
        ):
        setattr(config, attribute, not getattr(config, attribute))
    if icon:
        row.label(icon=icon, text="")
    elif icon_value:
        row.label(icon_value=icon_value, text="")
    if result is not None:
        result['dropdown_row'] = row

    return getattr(config, attribute)

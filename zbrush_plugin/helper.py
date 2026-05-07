# ZBRUSH MACRO - Recorded in ZBrush version 2026
import zbrush.commands as zbc


def import_stls(item_path) -> None:
    zbc.show_actions(0)
    zbc.config(2026)
    placeholder_obj = r"D:\chezmoi\scoop\persist\zbrush-np\placeholder.obj"
    zbc.set_next_filename(str(placeholder_obj))
    zbc.press("Tool:Import")
    zbc.press("ZPlugin:SubTool Master:Multi Append")


def prepare_snapshot(item_path) -> None:
    # zbc.press("Preferences:LightBox:LightBox")
    zbc.canvas_stroke(
        zbc.Stroke(
            """(ZObjStrokeV02n74=H94VF3H94VF5H95VF7H95VFAH97VFEH99V103H9BV108H9DV10BH9DV10CH9EV10CH9EV10DH9FV10FHA0V110HA0V112HA1V112HA1V113HA2V114HA2V115HA2V116HA3V116HA3V117HA4V117HA4V118HA5V119HA5V11BHA6V11BHA7V11DHA7V11FHA8V121HA8V123HA9V124HAAV126HAAV129HABV129HABV12BHABV12DHACV12DHACV12FHACV130HACV132HADV133HADV134HAEV135HAEV137HAEV138HAFV138HAFV139HAFV13AHAFV13BHB0V13CHB0V13DHB0V13EHB1V13FHB2V140HB2V141HB2V142HB3V143HB3V144HB4V145HB4V146HB4V147HB5V148HB5V149HB5V14AHB5V14BHB6V14CHB7V14EHB7V14FHB7V150HB8V152HB8V153HB8V154HB8V155HB8V155)""",
        ),
    )
    zbc.press("Transform: Edit")
    zbc.set_mod("Tool:SubTool:placeholder", 2)
    zbc.press("Transform:Fit")
    zbc.press("Color:Clear")


if __name__ == "__main__":
    zbc.add_button(
        "ZPlugin:SubTool Master:import_stls",
        "Press to run this macro.",
        import_stls,
    )
    zbc.add_button(
        "ZPlugin:SubTool Master:prepare_snapshot",
        "prepare_snapshot",
        prepare_snapshot,
    )

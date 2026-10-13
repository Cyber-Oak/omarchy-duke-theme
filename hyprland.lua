-- Duke — Hyprland side of the theme: borders, frosted glass, shadows, motion.
--
-- Hand-written instead of generated from default/themed/hyprland.lua.tpl,
-- which only emits border colours. A template never overwrites a file the
-- theme ships, so the border values below must be kept in step with
-- `hyprland_active_border` / `hyprland_inactive_border` in colors.toml.
--
-- Omarchy drops every *.lua from a theme it treats as untrusted (one cloned
-- by `omarchy theme install`, or any theme directory holding a .git), so this
-- file only loads with the symlink install described in the README.
--
-- Load order: default looknfeel (blur off) -> default windows (opacity
-- "0.985 0.96") -> this file -> ~/.config/hypr/looknfeel.lua (user wins).
-- Glass recipe after devsviat/omarchy-abstract-black-theme.

---@diagnostic disable-next-line: undefined-global
local hl = hl
---@diagnostic disable-next-line: undefined-global
local o = o

-- colors.toml hyprland_active_border: accent at the top, dim green below.
local active_border_color = { colors = { "rgba(1fe81fee)", "rgba(0e6e0e99)" }, angle = 90 }
-- colors.toml hyprland_inactive_border.
local inactive_border_color = "rgba(1e2a1e99)"

hl.config({
  general = {
    gaps_in = 4,
    gaps_out = 9,
    border_size = 2,

    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    -- Soft, console-era rounded panels. The shell reads this radius too, so
    -- bar popups, menus and notifications follow.
    rounding = 12,
    rounding_power = 2.5,

    -- A faint green halo rather than a black drop shadow: panels glow a little
    -- against the dark wallpaper.
    shadow = {
      enabled = true,
      range = 24,
      render_power = 3,
      offset = { 0, 4 },
      color = "rgba(0a3a0a99)",
      color_inactive = "rgba(04050466)",
    },

    -- Frosted glass: three passes at size 9 is wide and smooth without banding.
    -- Vibrancy is modest — the wallpapers are already saturated green and a
    -- higher value pushes the blur toward neon.
    blur = {
      enabled = true,
      size = 9,
      passes = 3,
      noise = 0.015,
      contrast = 1.0,
      brightness = 0.85,
      vibrancy = 0.2,
      vibrancy_darkness = 0.3,
      new_optimizations = true,
      xray = false,
      ignore_opacity = true,
      special = true,
      popups = true,
      popups_ignorealpha = 0.5,
    },
  },
})

-- Motion: a quick pop for windows, a smooth glide for everything that moves.
hl.curve("dukePop", { type = "bezier", points = { { 0.16, 1 }, { 0.3, 1.06 } } })
hl.curve("dukeGlide", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.curve("dukeOut", { type = "bezier", points = { { 0.6, 0.04 }, { 0.98, 0.34 } } })

hl.animation({ leaf = "windowsIn", enabled = true, speed = 4, bezier = "dukePop", style = "popin 80%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 2.5, bezier = "dukeOut", style = "popin 80%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 4, bezier = "dukeGlide", style = "slide" })
hl.animation({ leaf = "border", enabled = true, speed = 6, bezier = "dukeGlide" })
hl.animation({ leaf = "fadeSwitch", enabled = true, speed = 4, bezier = "dukeGlide" })
hl.animation({ leaf = "fadeShadow", enabled = true, speed = 4, bezier = "dukeGlide" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "dukeGlide", style = "slidefade 20%" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 3, bezier = "dukeGlide", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 2, bezier = "dukeOut", style = "fade" })

-- Window translucency (active, inactive). Browsers, video players, games and
-- screen-share targets drop the default-opacity tag in Omarchy's app rules and
-- stay opaque.
o.window({ tag = "default-opacity" }, { opacity = "0.92 0.85" })

-- Terminals carry alpha on the cell background only (ghostty.conf,
-- alacritty.toml, kitty.conf, foot.ini), so text stays fully opaque. Window
-- opacity on top would fade the glyphs too, so keep them at 1.0 when focused.
o.window({ tag = "terminal" }, { opacity = "1.0 0.95" })

-- Blur behind the Omarchy shell's layer surfaces; their alpha comes from the
-- shell.*.toml files. The bar only skips its fully transparent edges.
hl.layer_rule({ match = { namespace = "^omarchy-bar$" }, blur = true, blur_popups = true, ignore_alpha = 0.15 })

-- Full-screen layers are a light scrim with a card on top. A 0.55 threshold
-- sits between them: only the card frosts, the desktop around it stays sharp.
hl.layer_rule({
  match = {
    namespace = "^(omarchy-menu|omarchy-notifications|omarchy-osd|omarchy-polkit|omarchy-clipboard|omarchy-emojis|omarchy-keyboard-panel|omarchy-reminders|omarchy-network-qr|omarchy-image-selector)$",
  },
  blur = true,
  blur_popups = true,
  ignore_alpha = 0.55,
})

%global origname glide
%global appid    net.base_art.Glide

Name:           glide-rs
Version:        0.6.9
Release:        3%{?dist}
Summary:        Minimalistic media player based on GStreamer and GTK4

License:        MIT
URL:            https://github.com/philn/glide
Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz
# The crates the build needs, vendored: Copr builds have no network access and
# neither does mock. Regenerate with ./vendor.sh after every version bump.
Source1:        %{name}-%{version}-vendor.tar.xz

# A size request on the video widget is a *minimum* size, so a video taller
# than the screen cannot shrink and is clipped in fullscreen. Not yet sent
# upstream.
Patch0:         0001-Do-not-force-the-video-widget-to-the-video-s-own-siz.patch
# Local preference: bare arrow and page keys seek by mpv's default steps.
Patch1:         0002-Bind-the-bare-arrow-and-page-keys-to-mpv-s-seek-step.patch
# The position label formatted the playback rate as "1.25.x".
Patch2:         0003-Print-the-playback-rate-as-1.25x-not-1.25.x.patch

BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  meson
BuildRequires:  gettext
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gtk4) >= 4.14
BuildRequires:  pkgconfig(libadwaita-1) >= 1.5
BuildRequires:  pkgconfig(gstreamer-1.0) >= 1.20
BuildRequires:  pkgconfig(gstreamer-play-1.0) >= 1.20
BuildRequires:  pkgconfig(gstreamer-video-1.0) >= 1.20
BuildRequires:  pkgconfig(gstreamer-pbutils-1.0) >= 1.20
# build.rs emits -lX11 for linux targets
BuildRequires:  pkgconfig(x11)

Requires:       hicolor-icon-theme
Requires:       gstreamer1-plugins-good%{?_isa}

# https://docs.fedoraproject.org/en-US/quick-docs/assembly_installing-plugins-for-playing-movies-and-music/
Recommends:     gstreamer1-libav
Recommends:     gstreamer1-plugins-ugly-free

%description
Glide is a simple and minimalistic media player relying on GStreamer for the
multimedia support and GTK4 for the user interface. It plays any multimedia
format supported by GStreamer, locally or remotely hosted, and supports
subtitles, audio and video track selection, and audio visualization.

Video is rendered through the gtk4paintablesink element, which is compiled into
the binary and registered at startup rather than loaded from the GStreamer
plugin path.

%prep
%autosetup -n %{origname}-%{version} -a1 -p1
%cargo_prep -v vendor

%build
# build.rs uses vergen-gitcl, and a release tarball carries no .git
export VERGEN_IDEMPOTENT=1
%meson
%meson_build

%install
%meson_install
%find_lang %{origname}

%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/%{appid}.metainfo.xml
desktop-file-validate %{buildroot}%{_datadir}/applications/%{appid}.desktop

# The video sink is a compiled-in static plugin (gstgtk4::plugin_register_static
# in src/main.rs), not an RPM dependency. If gst-plugin-gtk4 ever drops out of
# the build there is no sink at all, and nothing fails until playback. Count
# rather than pipe into grep -q: a crashing strings would otherwise leave the
# pipeline's status to grep, and the count keeps %%check's -x trace small.
sink=$(strings %{buildroot}%{_bindir}/%{origname} | grep -c gtk4paintablesink || :)
test "$sink" -ge 1

# Patch0: no size request survives on the video widget. Positive control
# first, so the count below cannot pass by grepping a file that moved.
grep -q video_renderer src/ui_context.rs
sizereq=$(cat src/*.rs | grep -c set_size_request || :)
test "$sizereq" -eq 0

# Patch1: six mpv-style seek accelerators, in the table and in the binary.
accels=$(grep -cE '\("seek\(-?[0-9]+\)"' src/ui_context.rs || :)
test "$accels" -eq 6
# Rust string literals carry a length instead of a NUL, so .rodata runs them
# together ("...<Primary>Upaudio-volume-increase<Primary>Down..."): match
# substrings, never whole lines, and count the distinct offsets.
binaccels=$(strings %{buildroot}%{_bindir}/%{origname} | grep -oE 'seek\(-?[0-9]+\)' | sort -u | wc -l)
test "$binaccels" -eq 6
# The action must declare the type g_action_parse_detailed_name() produces
# for a bare integer, which is int32. Declaring INT64 makes GTK refuse every
# activation on a type mismatch and the keys do nothing, visibly identical
# to the accelerators never having been bound at all.
grep -q 'SimpleAction::new("seek"' src/main.rs
inttype=$(grep -c 'SimpleAction::new("seek", Some(glib::VariantTy::INT32))' src/main.rs || :)
test "$inttype" -eq 1

# Patch2: the playback rate reads "1.25x", never "1.25.x".
grep -q 'playback_rate:.2' src/main.rs
straydot=$(grep -c '{playback_rate}\.x' src/main.rs || :)
test "$straydot" -eq 0

%files -f %{origname}.lang
%license LICENSE
%doc README.md TODO
%{_bindir}/%{origname}
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{appid}.svg
%{_metainfodir}/%{appid}.metainfo.xml

%changelog
* Wed Sep 09 2026 Erik Berg <fedora@slipsprogrammor.no> - 0.6.9-3
- Fix Patch1: the seek action declared an int64 parameter, but a detailed
  action name parses a bare integer as int32, so GTK refused every
  activation and the new keys silently did nothing
- Add Patch2: print the playback rate as "1.25x" rather than "1.25.x"

* Wed Sep 09 2026 Erik Berg <fedora@slipsprogrammor.no> - 0.6.9-2
- Add Patch0: do not set a size request on the video widget, which clipped
  videos taller than the screen in fullscreen (1080x1920 on a 1080p display)
- Add Patch1: bind the bare arrow and page keys to mpv's seek steps, moving
  playback speed to Ctrl+Page_Up/Page_Down

* Wed Sep 09 2026 Erik Berg <fedora@slipsprogrammor.no> - 0.6.9-1
- Initial package: Glide 0.6.9, GStreamer/GTK4 media player written in Rust
- Crates are vendored into the SRPM (Source1, ./vendor.sh) because neither
  Copr nor mock gives the build network access

%global origname glide
%global appid    net.base_art.Glide

Name:           glide-rs
Version:        0.6.9
Release:        1%{?dist}
Summary:        Minimalistic media player based on GStreamer and GTK4

License:        MIT
URL:            https://github.com/philn/glide
Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz
# The crates the build needs, vendored: Copr builds have no network access and
# neither does mock. Regenerate with ./vendor.sh after every version bump.
Source1:        %{name}-%{version}-vendor.tar.xz

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
%autosetup -n %{origname}-%{version} -a1
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

%files -f %{origname}.lang
%license LICENSE
%doc README.md TODO
%{_bindir}/%{origname}
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{appid}.svg
%{_metainfodir}/%{appid}.metainfo.xml

%changelog
* Wed Sep 09 2026 Erik Berg <fedora@slipsprogrammor.no> - 0.6.9-1
- Initial package: Glide 0.6.9, GStreamer/GTK4 media player written in Rust
- Crates are vendored into the SRPM (Source1, ./vendor.sh) because neither
  Copr nor mock gives the build network access

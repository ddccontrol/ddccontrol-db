When generating database entries from ddccontrol scannings, always read this:

Using the ddccontrol output from this GitHub issue, generate a conservative and minimally-assumptive monitor XML profile for ddccontrol-db.

Requirements:

* Create a new monitor XML file using the monitor PNP ID from the issue.
* Add a comment header at the top referencing the GitHub issue URL.
* Keep the XML style consistent with existing monitor definitions in the repository.
* Include `<include file="VESA"/>`.

Very important rules:

* Only treat controls with explicit non-`???` names in the ddccontrol output as known controls.
* Do NOT invent semantic mappings for controls marked as `???`.
* Do NOT infer monitor-specific enum values (such as input source mappings) unless they are explicitly confirmed by the issue itself.
* If values are borrowed from similar Dell monitor profiles, clearly label them as unverified candidate mappings.
* Unknown controls from the issue should remain present in the XML file, but commented out for future investigation.
* Prefer a conservative database entry over an aggressive one.
* Do not expose potentially destructive controls such as factory reset as active controls unless already standardized in existing ddccontrol-db Dell profiles.

Git workflow requirements:

* Create a new branch for the issue.
* Commit the generated XML file.
* Use a commit message containing:
  Fixes #<issue-number>
* Open a PR with a description explaining that:

  * the profile is intentionally conservative,
  * candidate mappings are commented out,
  * and hardware verification is requested from the issue author before enabling additional controls.

The goal is to create a safe initial profile suitable for distribution in packages without risking incorrect monitor-specific mappings.

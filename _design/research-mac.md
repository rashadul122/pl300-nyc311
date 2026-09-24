# Research: mac

Research on Power BI for a Mac user, checked on 2026-09-22, mostly against Microsoft primary sources.

(1) Power BI Desktop is officially supported on Windows on ARM if the Windows 11 PC has KB5065789 (the September 2025 update). But Microsoft only ships an x64 build: the Download Center offers only PBIDesktopSetup_x64.exe (v2.157.1354.0, published 9/3/2026). On an Apple Silicon virtual machine it therefore runs through Windows' x64 emulation. Microsoft names only Parallels 18/19/20 as authorized for Windows 11 on Arm on Apple Silicon Macs. VMware Fusion has been free for all users, including commercial use, since 11 Nov 2024, but Microsoft does not list it. UTM has no 3D acceleration for Windows.

(2) The browser (Power BI service) can now create semantic models through Power Query Online, run the full Power Query editor for import models, and edit relationships, measures, calculated columns and tables, row-level security, date tables and Model Options (July 2026). It also has DAX query view and TMDL view (TMDL view on the web is still in preview, since July 2026) and can create reports. Limits: DAX query view and TMDL view need write permission on the semantic model; scripts and queries are thrown away when you close them; changes auto-save with no undo (version history exists); some connectors are unsupported; dynamic data sources don't work.

(3) Personal email addresses (Gmail, Outlook.com) cannot sign up for the Power BI service; Desktop works without signing in. Ways to get a work account:
- a Microsoft 365 (Office 365 E5) trial, which needs a credit card and lasts 30 days;
- an Azure free account, which creates a Microsoft Entra tenant where you add your own user. This is reported by the community and was not tested;
- the Microsoft 365 Developer Program sandbox. A personal account can join the program, but the sandbox itself now requires a qualifying path (Visual Studio Pro/Enterprise standard subscription, a partner program, or Premier/Unified support) plus a billing account. Its terms also allow development use only.

A Fabric trial needs a work account first. It lasts 60 days and does not include Copilot or AI features.

(4) Publish to web makes the data public: anyone can reach the underlying model data. A Power BI admin must allow it; since January 2020 the default allows only existing embed codes. In a tenant you create yourself, you are the admin. Microsoft's documents contradict each other on whether a Free license can create embed codes from My workspace. Several features don't work with it, including Key Influencers, row-level security, report-level measures, DirectQuery, R/Python visuals and Q&A.

(5) A Free license can build and refresh content in My workspace (up to 8 scheduled refreshes a day, 1 GB per semantic model on shared capacity). It cannot share, work in shared workspaces, use Copilot (which needs a paid F2 or higher / P1 capacity; Pro or PPU alone is not enough, and trials are excluded) or use Git integration (needs a Fabric capacity; a trial capacity works).

Several claims in the owner's blueprint are wrong and should be corrected. Details and sources are in the report.

## Findings

- [verified] Power BI Desktop minimum requirements (Learn, ms.date 2026-07-22): Windows 10 / Server 2016 or later; 'For Windows on ARM, the 2025-09 Cumulative Update is required (KB5065789)'; .NET 4.7.2+; WebView2; display at least 1440x900; Windows display scaling above 100% can hide dialogs you need; CPU '1 GHz 64-bit (x64) processor or better recommended'; the 32-bit version is no longer supported.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop)
- [verified] Microsoft ships no native ARM64 installer. The Download Center offers only PBIDesktopSetup_x64.exe (version 2.157.1354.0, published 9/3/2026, 661.8 MB), and its system requirements still say 'available for 64-bit (x64) platforms'. On Windows on ARM (including an Apple Silicon VM) Desktop therefore runs under Windows' Prism x64 emulation.  (https://www.microsoft.com/en-us/download/details.aspx?id=58494 (read in browser 2026-09-22))
- [verified] The October 2025 feature summary says Desktop 'is now supported on Windows on ARM PCs that have the 2025-09 Cumulative Update installed (KB5065789)'. A Microsoft employee marked the ARM Fabric Idea COMPLETED on that basis. A community thread from about May 2026 reports that both the Store and the Download Center only ever install the x64 build; its accepted answer (by a community member, not Microsoft) says no ARM64 installer is documented.  (https://powerbi.microsoft.com/en-us/blog/power-bi-october-2025-feature-summary/ ; https://community.fabric.microsoft.com/t5/Fabric-Ideas/Make-power-BI-desktop-fully-compatible-with-ARM-CPU-such-as/idi-p/4681097 ; https://community.fabric.microsoft.com/t5/Desktop/Power-BI-Native-ARM-on-Windows-11-ARM-edition/m-p/5176254)
- [verified] Microsoft names only Parallels Desktop 18, 19 and 20 as 'authorized solutions' for Arm versions of Windows 11 Pro/Enterprise on M-series Macs; Windows 365 Cloud PC is the other option it mentions. Stated limits: DirectX 12 apps may fail, 32-bit Arm Store apps are unsupported, and there is no nested virtualization (so no WSL, Windows Sandbox or VBS). VMware Fusion is not listed.  (https://support.microsoft.com/en-us/windows/options-for-using-windows-11-with-mac-computers-with-apple-m1-m2-and-m3-chips-cd15fd62-9b34-4b78-b0bc-121baa3c568c)
- [verified] VMware Fusion and Workstation have been free for commercial, educational and personal users since 11 Nov 2024; ticket support was dropped. This corrects the blueprint's 'free for personal use'.  (https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/)
- [likely] UTM has no GPU/3D acceleration for Windows guests (software rendering via virtio-gpu/SPICE). Its own docs note a Windows 11 24H2 graphics-driver compatibility workaround and a libslirp ping/network quirk.  (https://docs.getutm.app/guides/windows/ ; https://github.com/utmapp/UTM/discussions/3610)
- [verified] Microsoft offers an official Windows 11 Arm64 ISO and says its primary use is creating VMs, including on Apple Silicon Macs. A product key or licence is still needed to activate the edition.  (https://learn.microsoft.com/en-us/windows/arm/iso ; https://www.microsoft.com/en-us/software-download/windows11arm64)
- [likely] Known VM issues: the Parallels KB (last reviewed June 2025) lists 'Error fetching data for this visual' as a known issue of Power BI on Arm. Its suggested workaround (use the 32-bit build) is obsolete because 32-bit is no longer supported. A community Super User reports running Desktop in Parallels on M2/M4 Macs for about 3.5 years, needing only Coherence mode during install.  (https://kb.parallels.com/en/129794 ; https://community.fabric.microsoft.com/t5/Desktop/Power-BI-Native-ARM-on-Windows-11-ARM-edition/m-p/5177718)
- [verified] Microsoft's virtualization statement is ambiguous for local VMs. Desktop is 'fully supported' on Azure Virtual Desktop and Windows 365, while 'Citrix VDI and other virtual desktop environments, excluding AVD and W365, aren't supported'. It does not explicitly cover a local Parallels, Fusion or UTM VM.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop)
- [verified] Browser web modeling (Learn, ms.date 2026-08-14) supports: creating import semantic models via Get Data / Power Query Online (then 'Create a report' or 'semantic model only'); the full Power Query editor through 'Transform data' for import models; measures, calculated columns and calculated tables with IntelliSense; relationships; properties; mark as date table; row-level security roles (DAX editor for dynamic rules); layouts; refresh options; creating new reports. Changes auto-save with no undo; semantic model version history is supported.  (https://learn.microsoft.com/en-us/power-bi/transform-model/service-edit-data-models)
- [verified] Web modeling limitations. Power Query editor: no custom connectors, R, Python, OLE DB, Essbase or HDFS; dynamic data sources unsupported; personal cloud connections can't be created in the editor; no editor for incremental-refresh models; relationships from the source aren't imported. Models that can't be opened: not in enhanced metadata format, live connection, automatic aggregations. Missing from the web: feature tables, Q&A/synonyms setup, View as, sensitivity classification, barcode category. Permissions: write permission is needed to edit; only the model owner can use Get data to add tables. The admin setting for web editing must be on.  (https://learn.microsoft.com/en-us/power-bi/transform-model/service-edit-data-models)
- [verified] DAX query view in the web: open it with 'Write DAX queries'. It needs write permission on the semantic model and the workspace setting 'User can edit data models in the Power BI service (preview)'. Queries are discarded on close; at most 99,999 rows per query; DEFINE MEASURE plus 'Update model with changes' can write measures back to the model, and /// comments become measure descriptions.  (https://learn.microsoft.com/en-us/power-bi/transform-model/dax-query-view)
- [verified] TMDL view on the web is in Preview (announced in the July 2026 feature summary). It can script, preview (as a diff) and apply createOrReplace TMDL against a published semantic model. It needs write permission, has separate View and Edit modes, doesn't keep scripts, and supports version history for rollback. Applying metadata does not refresh data.  (https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view ; https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/Power-BI-July-2026-Feature-Summary/ba-p/5303533)
- [verified] Model Options (type detection, relationship autodetect, auto date/time, parallel loading, import locale, DirectQuery options) became editable in the web in July 2026.  (https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/Power-BI-July-2026-Feature-Summary/ba-p/5303533)
- [unverified] A Free-licence user can edit semantic models in the web (web modeling) inside My workspace. The Free feature table marks 'Datasets: Add, delete, edit' and 'Create a report' as available in My workspace only, but the web-modeling page is silent on My workspace, so this is unconfirmed.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/end-user-features)
- [verified] Consumer email cannot be used. Learn says a work or school email is required and consumer accounts (Gmail, Hotmail) can't be used directly; the FAQ says sign-up 'doesn't accept consumer email domains'.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi ; https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-sign-up-help)
- [verified] Microsoft's documented route without a work email: a Microsoft 365 (Office 365 E5) trial. It creates an onmicrosoft.com work account and a new tenant with you as admin, up to 25 licences, requires a credit card, and must be cancelled before 30 days to avoid charges. Power BI Pro is included in Microsoft 365 E5 and Office 365 E5.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-sign-up-help ; https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing)
- [verified] The Learn sign-up page says 'Microsoft 365 Business Premium trials include Power BI Pro'. This conflicts with Microsoft's pricing page, which lists Pro as included only in Microsoft 365 E5 / Office 365 E5. Treat the Business Premium claim as wrong until tested.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi vs https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing)
- [likely] Azure free-account route: an Azure free account created with a personal Microsoft account generates an Entra tenant (onmicrosoft.com); you create a member user there and use it to sign in to Power BI / Fabric. The Entra docs confirm that people needing a tenant 'can sign up for a free account'. That the resulting user works in Power BI is community-reported (accepted answer, Sept 2026); not tested. The Azure free account needs a credit/debit card and phone for identity verification (possible $1 temporary hold), gives $200 credit for 30 days, and is limited to one per new customer.  (https://learn.microsoft.com/en-us/entra/fundamentals/create-new-tenant ; https://community.fabric.microsoft.com/discussions/power-bi-web-app/how-can-i-get-free-microsoft-tenant-id/5366507 ; https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)
- [verified] Microsoft 365 Developer Program (FAQ ms.date 2026-09-04): a personal Microsoft account can join the program, but the E5 sandbox is available only to eligible members: Visual Studio Pro/Enterprise standard subscribers (monthly plans not eligible), ISV Success / Microsoft AI Cloud Partner Program tiers (including Action Pack and Launch Benefits), or Premier/Unified Support customers. Setup requires an active MCA billing account with an active Azure subscription and no spending limit. The sandbox includes Power BI Pro (not Premium), renews every 90 days based on development activity, and is 'for development purposes only'.  (https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-faq ; https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-get-started)
- [verified] Fabric trial (ms.date 2026-08-12): 60 days, F4 or F64, plus a complimentary Power BI Individual Trial with PPU-equivalent rights. New users must first get a Fabric (Free) per-user licence, so a work account is required. Not supported on trial: Copilot, AI experiences (data agent, AI functions), Private Link. Trials per tenant are limited, repeat trials aren't guaranteed, and after expiry non-Power BI items are deleted after 7 days.  (https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial)
- [verified] Publish to web warning: 'anyone on the Internet can view your published report... Viewing requires no authentication... anyone can access the underlying data in your model even if your report does not display it.'  (https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web)
- [verified] Publish to web requires the admin tenant setting. Only admins can allow new embed codes; since the week of 27 Jan 2020 the default is 'Allow only existing embed codes', so users can't create new codes until an admin switches to 'Allow existing and new codes'. The Fabric administrator role (or the Power BI admin) manages it; in a self-created tenant the creator is Global Administrator.  (https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-export-sharing ; https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/Heads-up-The-Publish-to-web-default-is-changing-and-it-affects/ba-p/5175938 ; https://learn.microsoft.com/en-us/entra/fundamentals/create-new-tenant)
- [verified] Microsoft's docs conflict on Publish to web licensing. The Publish to web page says 'You need a Microsoft Power BI license to publish to web from My Workspace' (Pro/PPU for workspaces). The Free-user feature table (ms.date 2026-05-26) says 'Publish to web embed code creation requires Pro or PPU. Free users cannot create embed codes.' Also, the embed code keeps working only while its creator keeps access, including any Pro/PPU licence the workspace requires.  (https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web ; https://learn.microsoft.com/en-us/power-bi/fundamentals/end-user-features)
- [verified] Publish to web does not support: RLS, DirectQuery, Live Connection, shared/certified semantic models in another workspace, report-level DAX measures, R/Python visuals, Q&A, export data, paginated reports, mobile layout, multi-language reports. Data is cached for 1 hour. The Key Influencers visual separately lists Publish to web as unsupported.  (https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web ; https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-influencers)
- [verified] Fabric (Free) licence: creates and views content for yourself in My workspace (including scheduled refresh, create a report, Analyze in Excel, export, self-subscriptions). It can consume shared content only on F64+/Premium capacity with the Viewer role, cannot share or collaborate, cannot publish to other workspaces, and does not expire.  (https://learn.microsoft.com/en-us/power-bi/fundamentals/end-user-features ; https://learn.microsoft.com/en-us/power-bi/fundamentals/service-features-license-type ; https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-sign-up-help)
- [likely] Shared capacity (Free/Pro) limits: maximum imported semantic model size in the service is 1 GB; 8 scheduled refreshes per day; 10 GB uncompressed-data processing limit during refresh.  (https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-data)
- [verified] Copilot in Power BI requires a paid Fabric capacity (F2 or higher) or Premium P1 or higher; 'Trial capacities and free SKUs aren't supported'; 'A Power BI Pro or PPU license alone isn't sufficient'. Desktop Copilot needs write access to a workspace on such a capacity. F2 pay-as-you-go is about $0.36/hour (about $263/month if always on) and can be paused (third-party figure).  (https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction ; https://www.alphabold.com/microsoft-fabric-pricing-and-licensing/)
- [verified] Prices (US, paid yearly): Power BI Pro $14/user/month, PPU $24/user/month; the Free account needs no credit card.  (https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing)
- [verified] Key Influencers limitations: no DirectQuery, no live connection to AAS/SSAS, no Publish to web, no SharePoint Online embedding, and it cannot analyze a categorical metric when the model sets Discourage Implicit Measures = true (for example when calculation groups exist). Anomaly detection: line charts with a time-series axis only; no legend, multiple values or secondary values; at least 4 points; available in both Desktop and the service.  (https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-influencers ; https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-anomaly-detection)
- [verified] PBIP can be deployed from macOS without Desktop using fabric-cicd, Microsoft's officially supported open-source Python library that calls the Fabric REST APIs (Python 3.9–3.13 per its site; interactive browser login or service principal; needs the Contributor workspace role). The Fabric REST API also accepts semantic model definitions in TMDL (definition.pbism + definition/ folder).  (https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-deploy-fabric-cicd ; https://microsoft.github.io/fabric-cicd/latest/ ; https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition)
- [unverified] Not established: whether the Fabric REST API / fabric-cicd can deploy semantic models and reports to a Pro (shared-capacity) workspace or to My workspace. The API page only says the user 'must have the appropriate license'. A Fabric trial capacity is a safe target.  (https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model)
- [verified] Fabric Git integration (GitHub or Azure DevOps; semantic models and reports in preview) requires a Fabric capacity (a trial is allowed) or a Premium capacity, plus tenant switches. GitHub connects with a PAT.  (https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started ; https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration)
- [verified] The on-premises data gateway is Windows-only (Windows 10/11 or Server 2019+, .NET 4.8) and needs a work account. A Mac cannot host a gateway, so a scheduled service refresh cannot reach the local 26 GB SQLite file without a Windows machine (the VM would have to stay on).  (https://learn.microsoft.com/en-us/data-integration/gateway/service-gateway-install)
- [verified] NYC 311 data is available live through the anonymous Socrata SODA API (dataset erm2-nwe9, now titled '311 Service Requests from 2020 to Present', 48 fields, updated 2026-09-22). API field names differ from the local DB columns (complaint_type vs problem_formerly_complaint_type; descriptor vs problem_detail_formerly_descriptor). This makes it a gateway-free, refreshable 'API not static Excel' source.  (curl https://data.cityofnewyork.us/resource/erm2-nwe9.json?$limit=1 and https://data.cityofnewyork.us/api/views/erm2-nwe9.json (run 2026-09-22))
- [likely] Power BI Desktop can be used without signing in or having a work account; an account is needed only to publish or use the service.  (https://learn.microsoft.com/en-us/answers/questions/5133271/how-to-use-powerbi-desktop-without-a-work-or-schoo)

## Details

# Power BI for a Mac user: what works in September 2026

Checked on 2026-09-22. Each claim is marked:
- **[V]**: verified. I read a primary source (Microsoft Learn, the Microsoft Download Center or pricing page, or the vendor's own page), or ran a command.
- **[L]**: likely. The claim comes from secondary or community sources that agree with each other.
- **[U]**: unverified. The claim is an assumption or the sources are silent.

Nothing here was run in Power BI.

---

## 1. Power BI Desktop in a Windows 11 ARM VM on Apple Silicon

**Native ARM64 build or x64 emulation? Emulation.**
- Microsoft now officially supports Desktop on Windows on ARM. The requirement is that Windows has the 2025-09 cumulative update, KB5065789 (for Windows 11 builds 26100/26200). **[V]**
  - Sources: the [Learn download page](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop) (ms.date 2026-07-22) and the [October 2025 feature summary](https://powerbi.microsoft.com/en-us/blog/power-bi-october-2025-feature-summary/).
  - A Microsoft employee marked the ARM [Fabric Idea](https://community.fabric.microsoft.com/t5/Fabric-Ideas/Make-power-BI-desktop-fully-compatible-with-ARM-CPU-such-as/idi-p/4681097) "COMPLETED" on that basis.
- Microsoft ships only an x64 installer. **[V]**
  - The [Download Center](https://www.microsoft.com/en-us/download/details.aspx?id=58494) lists **PBIDesktopSetup_x64.exe**, version 2.157.1354.0, published 9/3/2026, 661.8 MB.
  - Its system requirements say "available for 64-bit (x64) platforms". The same text still mentions Internet Explorer 10, so it is out of date.
  - The Learn page also says CPU "1 GHz 64-bit (x64)".
- A [community thread](https://community.fabric.microsoft.com/t5/Desktop/Power-BI-Native-ARM-on-Windows-11-ARM-edition/m-p/5176254) from about May 2026 reports that the Store and the Download Center always install x64. Its accepted answer is from a community member, not Microsoft. **[V]** that the thread says this.
- **Conclusion:** "Supported on ARM" means the x64 build running under Windows' Prism emulation, not a native ARM64 app.

**Which hypervisor**
- **Parallels Desktop.** Microsoft names Parallels 18, 19 and 20 as the *only* "authorized solutions" for Windows 11 Pro/Enterprise on Arm on M-series Macs. **[V]** ([Microsoft support page](https://support.microsoft.com/en-us/windows/options-for-using-windows-11-with-mac-computers-with-apple-m1-m2-and-m3-chips-cd15fd62-9b34-4b78-b0bc-121baa3c568c))
  - The page's limits: DirectX 12 apps may fail; no 32-bit Arm Store apps; no nested virtualization, so no WSL, Windows Sandbox or VBS.
  - The version list probably trails current Parallels releases. **[U]**
- **VMware Fusion.** Free for commercial, educational and personal users since 11 Nov 2024. There is no ticket support. **[V]** ([VMware blog](https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/))
  - Microsoft does not list it as authorized.
  - The blueprint's "free for personal use" is out of date.
- **UTM.** Free, but it has **no 3D/GPU acceleration** for Windows guests. **[L]** ([UTM discussion](https://github.com/utmapp/UTM/discussions/3610))
  - Its [docs](https://docs.getutm.app/guides/windows/) mention a Windows 11 24H2 graphics-driver workaround and that ping doesn't work (a libslirp limitation).
- **Windows itself.** Microsoft hosts an official [Windows 11 Arm64 ISO](https://learn.microsoft.com/en-us/windows/arm/iso) and says its main use is building VMs, including on Apple Silicon. You still need a licence or product key to activate it. **[V]**

**Known issues and caveats**
- The [Parallels KB](https://kb.parallels.com/en/129794) (last reviewed June 2025) lists "Error fetching data for this visual" as a known issue on Arm. **[L]**
  - Its workaround is to use the 32-bit build. That no longer works: Microsoft no longer supports 32-bit.
- A community Super User reports running Desktop in Parallels on M2/M4 Macs for about 3.5 years. The only special step was switching to Coherence mode during install. **[L]** ([thread](https://community.fabric.microsoft.com/t5/Desktop/Power-BI-Native-ARM-on-Windows-11-ARM-edition/m-p/5177718))
- **Display.** Desktop needs a resolution of at least 1440x900. Scaling above 100% can hide dialogs you must click. **[V]**
  - A VM on a Retina screen may default to 200% scaling. Use the VM's "scaled" mode or set Windows to 100%. **[U]** (this interaction is my inference)
- **Support scope is ambiguous.** Microsoft says Desktop is "fully supported" on Azure Virtual Desktop and Windows 365, and that "Citrix VDI and other virtual desktop environments" aren't supported. It never explicitly addresses a *local* Parallels, Fusion or UTM VM. **[V]** that the text says this.
  - So each part is supported on its own (Windows on ARM; Parallels for Windows 11 Arm), but the combination is not documented.

---

## 2. What browser (service) authoring supports today

| Capability | Status in the browser | Source |
|---|---|---|
| Create an import semantic model from Get Data (Power Query Online), then "Create a report" or "semantic model only" | Yes **[V]** | [Edit semantic models in the service](https://learn.microsoft.com/en-us/power-bi/transform-model/service-edit-data-models) (ms.date 2026-08-14) |
| Full Power Query editor ("Transform data") on import models | Yes; changes must be saved and applied explicitly **[V]** | same |
| Relationships, measures, calculated columns and tables, properties, mark as date table, layouts | Yes, with IntelliSense **[V]** | same |
| RLS roles | Yes; dynamic rules (USERPRINCIPALNAME) need the DAX editor **[V]** | same |
| Model Options (type detection, relationship autodetect, auto date/time, parallel loading, locale, DirectQuery options) | Yes, since July 2026 **[V]** | [July 2026 feature summary](https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/Power-BI-July-2026-Feature-Summary/ba-p/5303533) |
| DAX query view | Yes; see notes below **[V]** | [DAX query view](https://learn.microsoft.com/en-us/power-bi/transform-model/dax-query-view) |
| TMDL view | Yes, **Preview** since July 2026; see notes below **[V]** | [TMDL view](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view) |
| Create or edit reports in the browser | Yes, including AI visuals (Key Influencers and anomaly detection apply to Desktop and the service) **[V]** | same pages; visual docs |

DAX query view in the browser:
- Open it with "Write DAX queries".
- It needs **write permission** on the semantic model and the workspace setting "User can edit data models in the Power BI service (preview)".
- DEFINE MEASURE plus "Update model with changes" writes measures back to the model; `///` comments become measure descriptions.
- Queries are **discarded on close**, and each query returns at most **99,999 rows**.

TMDL view in the browser:
- It can script, preview (as a diff) and **apply `createOrReplace` TMDL** to a published model.
- It needs write permission and has separate View and Edit modes.
- Scripts are not persisted. Rollback uses semantic model version history.
- Applying TMDL changes metadata only; you must refresh data yourself.

**Limits in the browser** (all **[V]**, from the web-modeling page):
- Changes auto-save and cannot be undone. Version history exists for recovery.
- Power Query editor:
  - No custom connectors, R, Python, OLE DB, Essbase, Exchange or HDFS.
  - **Dynamic data sources are unsupported.**
  - You can't create personal cloud connections inside the editor.
  - Models with incremental refresh can't use the editor.
  - Relationships in the source are not imported.
- Models that can't be opened in the browser: non-enhanced-metadata models, live connection, automatic aggregations.
- Features missing from the browser: feature tables, Q&A and synonym setup, "View as", sensitivity classification, barcode data category.
- Only the model *owner* can use Get data to add tables.
- The "Edit in Desktop" option is Windows-only (Direct Lake models).
- **Unconfirmed:** whether web modeling works in *My workspace* on a Free licence. The Free feature table marks dataset add/edit and "Create a report" as available in My workspace, but the web-modeling page is silent. **[U]**

**Getting PBIP text into the service without Desktop**
- **fabric-cicd**: Microsoft's officially supported Python library, built on the Fabric REST APIs. **[V]** ([deploy guide](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-deploy-fabric-cicd); [library site](https://microsoft.github.io/fabric-cicd/latest/))
  - Python 3.9–3.13. Logs in through the browser or a service principal. Needs the Contributor workspace role.
  - The project venv is stdlib plus pandas/numpy only, so this would need a separate venv.
- **Fabric REST API**: accepts a semantic model definition in TMDL (`definition.pbism` plus a `definition/` folder). **[V]** ([definition format](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition))
  - Whether it works against a Pro (shared-capacity) workspace or My workspace is **not established**. The docs only say "appropriate license". **[U]**
- **Fabric Git integration** (GitHub via a PAT; semantic models and reports in preview) requires a **Fabric capacity** (a trial is fine) or a Premium capacity, plus tenant switches. **[V]** ([get started](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started))

**Reaching the data from the service**
- The on-premises data gateway is **Windows-only** (.NET 4.8) and needs a work account. **[V]** ([install page](https://learn.microsoft.com/en-us/data-integration/gateway/service-gateway-install))
  - So a service refresh cannot reach the local SQLite file without an always-on Windows machine.
- NYC 311 is available anonymously through **Socrata SODA**. **[V]** (checked with curl on 2026-09-22)
  - Dataset `erm2-nwe9`, now titled "311 Service Requests from 2020 to Present", 48 fields, updated 2026-09-22.
  - API field names differ from the local DB: `complaint_type` vs `problem_formerly_complaint_type`, `descriptor` vs `problem_detail_formerly_descriptor`.
  - A static base URL (as the web connector requires) keeps it clear of the "dynamic data source" limit. **[L]**

---

## 3. Sign-up: can a personal email use Power BI?

**No, not for the service.** **[V]**
- Learn: "you need a work or school email account. You can't use consumer email accounts (for example, Gmail or Hotmail) directly." ([sign-up page](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi), ms.date 2026-03-23)
- The [FAQ](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-sign-up-help) (ms.date 2026-08-24) says sign-up "doesn't accept consumer email domains."
- **Desktop works without signing in. [L]** (Microsoft Q&A answers)

| Option | Result | Cost / catch | Confidence |
|---|---|---|---|
| **Microsoft 365 (Office 365 E5) trial** | Creates an onmicrosoft.com work account and a **new tenant with you as admin**; up to 25 licences; E5 includes Power BI Pro | **Credit card required**; cancel before 30 days or you are charged | **[V]** (FAQ; [licensing guide](https://learn.microsoft.com/en-us/fabric/enterprise/powerbi/service-admin-power-bi-licensing); [pricing page](https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing)) |
| **Azure free account** | Creates an Entra tenant; add a member user and sign in to Power BI with it (Fabric Free, then trials) | Card and phone for identity verification (possible $1 temporary hold); one per new customer; $200 credit for 30 days | Tenant creation **[V]** ([Entra quickstart](https://learn.microsoft.com/en-us/entra/fundamentals/create-new-tenant): "Only paid customers can create a new Workforce tenant... [others] can sign up for a free account"); Power BI working with that user **[L]** (community-reported, Sept 2026 [thread](https://community.fabric.microsoft.com/discussions/power-bi-web-app/how-can-i-get-free-microsoft-tenant-id/5366507); not tested) |
| **Microsoft 365 Developer Program E5 sandbox** | 25 E5 licences **including Power BI Pro** (not Premium) | A personal account can *join* the program, but the **sandbox** needs a qualifying path (details below); **not realistically available to him** | **[V]** ([FAQ](https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-faq), ms.date 2026-09-04; [setup page](https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-get-started)) |
| **Fabric trial** | 60 days of F4/F64 capacity plus an individual trial with PPU-equivalent rights | Needs a work account and a Fabric (Free) licence first; **no Copilot or AI experiences**; limited trials per tenant; repeats not guaranteed; non-Power BI items deleted 7 days after expiry | **[V]** ([Fabric trial](https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial), ms.date 2026-08-12) |

Developer Program sandbox details (all **[V]**):
- Qualifying paths:
  - a Visual Studio Pro or Enterprise **standard** subscription (monthly plans don't qualify);
  - the ISV Success or Microsoft AI Cloud Partner Program tiers (including Action Pack and Launch Benefits);
  - Premier or Unified Support customers.
- Setup since 2026 also requires an **MCA billing account with an active Azure subscription and the spending limit removed**.
- The sandbox renews every 90 days based on development activity.
- It is "for development purposes only". Using it for other purposes violates the terms, which is a risk for a portfolio or consultancy demo.

**A documentation error to know about.** The Learn sign-up page says "Microsoft 365 Business Premium trials include Power BI Pro". Microsoft's pricing page lists Pro as included only in **Microsoft 365 E5 / Office 365 E5**. Treat the Business Premium claim as wrong. **[V]** (both pages read)

**Assumptions:**
- After a cancelled M365 trial, the tenant and a self-service Fabric (Free) licence probably persist. The FAQ confirms self-service Free licences don't expire. **[U]**
- A new Power BI Pro individual trial lasts 60 days. The licensing guide says "upgrade to a 60-day trial." **[V]**

---

## 4. Publish to web

- **The warning, quoted:** "anyone on the Internet can view your published report... Viewing requires no authentication... anyone can access the underlying data in your model even if your report does not display it." **[V]** ([Publish to web page](https://learn.microsoft.com/en-us/collaborate-share/service-publish-to-web))
- **Tenant setting.** It lives under Export and sharing, and only admins can allow new embed codes. **[V]** ([tenant settings page](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-export-sharing))
  - Since the week of 27 Jan 2020, "Choose how embed codes work" defaults to **"Allow only existing embed codes"**. Users trying to create a new code are told to contact the admin until it is switched to "Allow existing and new codes". **[V]** ([Microsoft blog](https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/Heads-up-The-Publish-to-web-default-is-changing-and-it-affects/ba-p/5175938))
  - The Fabric administrator role can act as Power BI admin. **[V]**
  - Whoever creates a tenant becomes its Global Administrator, so in his own trial or Azure tenant he can enable it himself. **[V]** for the Global Administrator role, **[L]** that it covers this setting.
- **Licence: the docs contradict each other.**
  - The Publish to web page says "You need a Microsoft Power BI license to publish to web from My Workspace", and Pro or PPU for other workspaces.
  - The [Free-user feature table](https://learn.microsoft.com/en-us/power-bi/fundamentals/end-user-features) (ms.date 2026-05-26) says "Publish to web embed code creation requires Pro or PPU. Free users cannot create embed codes."
  - Both statements **[V]**. The actual behaviour is **[U]**: test it in the tenant before building the portfolio around a $0 public link.
- **The creator must keep access.** An embed code works only while its creator keeps access, including any Pro or PPU licence the workspace requires; otherwise its status becomes "Infringed". A trial-based public link can therefore die when the trial ends. **[V]** for the rule, **[U]** for the trial consequence.
- **Not supported with Publish to web** **[V]**:
  - RLS, DirectQuery, Live Connection;
  - semantic models shared from another workspace, shared or certified models;
  - **report-level DAX measures**;
  - R and Python visuals, Q&A, export data, paginated reports, mobile layout, multi-language reports.
  - The **Key Influencers visual also lists Publish to web as unsupported** ([Key influencers page](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-influencers)).
  - Data is cached for one hour.

---

## 5. What a Free licence can and cannot do

**Can** (sources: [features by licence](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-features-license-type), [free-user features](https://learn.microsoft.com/en-us/power-bi/fundamentals/end-user-features), [FAQ](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-sign-up-help)):
- Use Desktop, with no account needed. **[L]**
- In the service, with a work account, inside **My workspace only** **[V]**:
  - add, edit and delete datasets;
  - create reports and paginated reports;
  - **schedule refresh**;
  - Analyze in Excel, export, subscribe yourself, Q&A, insights.
- Consume content shared to him on **F64+ or Premium capacity**, with the Viewer role. **[V]**
- The Free licence does not expire. **[V]**

**Cannot** **[V]**:
- share or collaborate, publish to other workspaces, create or edit apps, share externally;
- create Publish to web embed codes, according to the feature table (conflicting docs; see section 4);
- use Copilot:
  - it needs a **paid F2+ or P1 capacity**;
  - "Trial capacities and free SKUs aren't supported" and "A Power BI Pro or PPU license alone isn't sufficient" ([Copilot overview](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction), ms.date 2026-08-24);
  - F2 pay-as-you-go is about $0.36/hour and can be paused **[L]**;
- use Git integration, which needs a Fabric capacity.

**Shared-capacity limits** (Free and Pro) **[L]** ([refresh doc](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-data)):
- 1 GB maximum imported semantic model;
- 8 scheduled refreshes per day;
- 10 GB of uncompressed data processed per refresh.

A full 22.5M-row, 44-column import probably needs to be aggregated or narrowed to fit under 1 GB. **[U]**

**Prices (US, paid yearly):** Pro $14/user/month, PPU $24/user/month. **[V]** ([pricing page](https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing))

---

## Where the current blueprint is wrong

File: `<portfolio>/deliverables/Senior-Data-Analytics-Portfolio-Blueprint.md`, lines 242–269.

1. **"A Free Power BI license can... Publish to web from My Workspace"** (lines 252 and 263). This is contradicted by Microsoft's Free feature table, which says Free users can't create embed codes. The docs conflict, so it must be tested before the $0 plan relies on it.
2. **"What Free cannot do is scheduled refresh."** Wrong. Free *can* schedule refresh in My workspace. Pro's real value is sharing, workspaces and (per one doc) Publish to web.
3. **"Scheduled refresh + Copilot (optional): Power BI Pro $14"** (line 269). Wrong for Copilot. Copilot needs a paid F2+ or P1 capacity; Pro, PPU and Fabric trials don't qualify.
4. **Sign-up is never mentioned.** With only a Gmail address, the service path needs one of: an M365 E5 trial (credit card), an Azure free account tenant (card verification; community-reported), or a sandbox (not eligible).
5. **VMware Fusion "free for personal use"** is out of date. It is free for all users, but Microsoft authorizes only Parallels.
6. **Publish to web details are missing:**
   - the tenant default blocks new embed codes until an admin allows them;
   - Key Influencers and report-level measures don't work with it;
   - the creator must keep a licence or the link breaks.
7. **The data-access constraint is missing.** The gateway is Windows-only, so a service refresh can't reach the local SQLite file. The SODA API is a working gateway-free source.

## What this means for the PL-300 build

- **Validating PBIP text without Desktop.** Two routes, each needing an account plus the right workspace:
  - deploy with fabric-cicd to a Fabric-trial workspace (Pro workspace unconfirmed);
  - or paste TMDL scripts into the web TMDL view (preview) of a model he owns.
  - Then check measures in the web DAX query view.
- **Design traps:**
  - Setting `discourageImplicitMeasures` (which calculation groups force) blocks Key Influencers from analyzing a categorical metric.
  - Key Influencers can't be shown through Publish to web.
  - Anomaly detection needs a line chart with a time axis and no legend.
- **Copilot** can only be described in this build, not shown, unless he pays for F2 capacity (plus a Pro licence to author content in that workspace).

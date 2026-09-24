# Research: exam

The current official PL-300 outline (exam "Microsoft Power BI Data Analyst", certification "Microsoft Certified: Power BI Data Analyst Associate") is titled "Skills measured as of April 20, 2026". The live Microsoft Learn page says ms.date 2026-03-07 and was last updated 2026-03-20. I fetched it on 2026-09-22 and it matches the 2026-07-19 Wayback snapshot line for line, so no newer outline has been published. It has 4 functional groups: Prepare the data (25–30%), Model the data (25–30%), Visualize and analyze the data (25–30%), and Manage and secure Power BI (15–20%). They contain 11 objectives and 78 bullet skills, all listed verbatim and numbered below.

How the outline changed recently (I diffed the archived versions myself):
- **January 15, 2026:** four Copilot skills were added (narrative visual, create a report page, suggest page content, summarize the semantic model).
- **April 20, 2026:** four wording changes. DirectLake was added to the storage-mode choice, which is the only Fabric-specific term anywhere in the outline. Drillthrough now names pages, filters and buttons. The personalization bullet was reworded. "Workspace app" became "app".
- **October 21, 2024 (the last major rewrite):** added calculation groups, DAX query view, visual calculations, pivot/unpivot/transpose and "reducing granularity". Removed the Q&A feature, scorecards, custom visuals, Analyze in Excel, and implicit-to-explicit measures.
- **Terms that never appear:** Fabric, OneLake, PBIP, TMDL, Git, deployment pipelines and dataflows are not mentioned anywhere.

Two facts matter for the build:
- **Copilot needs paid capacity.** It requires paid Fabric F2+ or Premium P1+; trial capacities, free SKUs and a Pro/PPU licence alone are not enough. In Desktop you also need write access to a workspace on that capacity.
- **Q&A visual is being retired.** It is scheduled for deprecation in December 2026, and a September 14, 2026 secondary source says retirement moved to February 2027. The design should not rely on it. Key Influencers, Decomposition tree and anomaly detection are still in the docs' "AI-powered visuals" group.

## Findings

- [verified] Current PL-300 outline is headed 'Skills measured as of April 20, 2026'; page metadata ms.date 2026-03-07, updated_at 2026-03-20; live page on 2026-09-22 is identical to the 2026-07-19 Wayback snapshot (no newer outline).  (https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300 (curl + WebFetch 2026-09-22; diff vs http://web.archive.org/web/20260719183800/https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300))
- [verified] Functional groups and weights: Prepare the data 25–30%; Model the data 25–30%; Visualize and analyze the data 25–30%; Manage and secure Power BI 15–20%. 11 objectives, 78 bullet skills (17/16/30/15).  (https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300)
- [verified] April 20, 2026 changes vs Jan 15, 2026 (all rated 'Minor'): 'Choose between DirectQuery and Import' became 'Choose between DirectLake, DirectQuery, and Import'; 'Configure drill through navigation' became 'Configure drillthrough navigation, including pages, filters, and buttons'; 'Enable personalized visuals in a report' became 'Enable personalization in a report, including personalized visuals'; 'Configure and update a workspace app' became 'Configure and update an app'.  (diff of http://web.archive.org/web/20260303130039/https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300 vs live page)
- [verified] January 15, 2026 update added four Copilot skills: 'Create a narrative visual with Copilot', 'Use Copilot to create a new report page', 'Use Copilot to suggest content for a new report page' (Create reports, rated Major) and 'Use Copilot to summarize the underlying semantic model' (Identify patterns and trends, rated Minor).  (diff of Wayback 20250418190442 (April 21, 2025 outline) vs 20251221144344 (January 15, 2026 outline))
- [verified] October 21, 2024 was the last major rewrite: 'Deploy and maintain items' was renamed 'Manage and secure Power BI', 'Manage semantic models' was deleted, and 'Secure and govern Power BI items' was added. Added: DAX query view, calculation groups, visual calculations, pivot/unpivot/transpose, semi-structured to table, group and aggregate rows, reducing granularity, calculated columns/tables use cases. Removed: Q&A feature, scorecards/metrics, custom visual, Analyze in Excel, implicit-to-explicit measures, Dual mode, optimal data types, global file options.  (diff of Wayback 20240426174112 (April 23, 2024 outline) vs 20241221191215 (October 21, 2024 outline and its change log))
- [verified] The outline never mentions Fabric, OneLake, PBIP, TMDL, Git, deployment pipelines or dataflows. DirectLake (added April 2026) is the only Fabric-specific term. It uses 'semantic model' terminology throughout.  (text search of live study guide)
- [verified] Exam logistics: 100 minutes, proctored, passing score 700, may include interactive components; offered in English, Japanese, Chinese (Simplified), Korean, German, French, Spanish, Portuguese (Brazil), Chinese (Traditional), Italian; localized versions update ~8 weeks after English; certification renews annually via free online assessment; no retirement notice on the cert page.  (https://learn.microsoft.com/en-us/credentials/certifications/power-bi-data-analyst-associate/ and study guide)
- [verified] Copilot in Power BI requires 'Paid Fabric capacity (F2 or higher) or Power BI Premium (P1 or higher). Trial capacities and free SKUs aren't supported.' A Pro or PPU licence alone isn't sufficient. In Power BI Desktop, Copilot needs write access to a workspace on paid Fabric or Premium capacity (doc ms.date 2026-08-24).  (https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction)
- [verified] The Microsoft docs list the AI-powered visuals as Decomposition tree, Key influencers, Smart narrative and Anomaly detection. The Q&A visual is marked 'scheduled for deprecation in December 2026'.  (https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-types-for-reports-and-q-and-a (redirects to power-bi-visualizations-overview, updated 2026-08-20))
- [likely] Power BI Q&A retirement was extended: 'Beginning in February 2027, Q&A will no longer work in Power BI'. Existing Q&A visuals will show an error.  (https://msbitutor.blogspot.com/2026/09/power-bi-q-retirement-reminder-february.html (2026-09-14 republish of a Microsoft Fabric Community blog post; the original at community.fabric.microsoft.com returned 403))
- [verified] The Narrative (smart narrative) visual has a Copilot mode that requires a Copilot licence and a Custom mode (manual text plus dynamic values) that works without Copilot.  (https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-smart-narrative)
- [verified] Anomaly detection works in Desktop and the Service, on line charts with time-series data only. It needs at least 4 points and does not support legends, multiple or secondary values, or Forecast/Min/Max/Average/Median/Percentile lines. It can explain anomalies using configurable 'Explain by' fields.  (https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-anomaly-detection)

## Details

# PL-300 skills measured (current official outline)

**Exam:** PL-300 "Microsoft Power BI Data Analyst". **Certification:** Microsoft Certified: Power BI Data Analyst Associate.

**Outline version:** "Skills measured as of April 20, 2026".
- Page metadata: ms.date 2026-03-07, updated_at 2026-03-20.
- The live page, fetched 2026-09-22, is identical to the Wayback snapshot of 2026-07-19. No newer outline has been announced.
- The page still carries the boilerplate "We have included two versions of the Skills Measured objectives…", but only the April 20, 2026 version is shown.
- **Primary source:** https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300

**Standing notes on the page (verbatim):**
- "The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam."
- "Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used."

**Audience profile (summary):**
- Deliver actionable insights. Provide business value through easy-to-comprehend visuals. Enable others to do self-service analytics.
- Collaborate with analytics engineers and data engineers.
- Use Power BI to prepare, model, visualize and analyze data, and to manage and secure Power BI.
- "You should be proficient at using Power Query and Data Analysis Expressions (DAX)."

**Logistics** (from https://learn.microsoft.com/en-us/credentials/certifications/power-bi-data-analyst-associate/):
- 100 minutes, proctored, may include interactive components.
- Pass mark is 700.
- Offered in 10 languages. Localized versions update about 8 weeks after English.
- Renewed yearly through a free online assessment.
- No retirement notice.

## Skills at a glance
1. Prepare the data (25–30%)
2. Model the data (25–30%)
3. Visualize and analyze the data (25–30%)
4. Manage and secure Power BI (15–20%)

Numbering is **group.objective.skill**. Text is verbatim from the page. The tag in [brackets] is my own feasibility note for a Mac-only, text-first (PBIP/TMDL/M/DAX) build, not Microsoft's wording:
- **T** = can be authored as text in PBIP/TMDL/M/DAX
- **D** = needs the Power BI Desktop UI to perform or show
- **S** = needs the Power BI Service or a tenant
- **C** = needs paid Fabric/Premium capacity

## 1 Prepare the data (25–30%)
**1.1 Get or connect to data**
- 1.1.1 Identify and connect to data sources or a shared semantic model [T for M source; shared model needs S]
- 1.1.2 Change data source settings, including credentials and privacy levels [D/S; privacy levels are a Desktop/Service setting]
- 1.1.3 Choose between DirectLake, DirectQuery, and Import [T for partition mode; DirectLake needs Fabric/OneLake = C]
- 1.1.4 Create and modify parameters [T: M parameters in expressions.tmdl]

**1.2 Profile and clean the data**
- 1.2.1 Evaluate data, including data statistics and column properties [D: column quality/distribution/profile; can be mirrored by a Python profile]
- 1.2.2 Resolve inconsistencies, unexpected or null values, and data quality issues [T]
- 1.2.3 Resolve data import errors [T for try/otherwise and Replace Errors; D to show the error UI]

**1.3 Transform and load the data**
- 1.3.1 Select appropriate column data types [T]
- 1.3.2 Create and transform columns [T]
- 1.3.3 Group and aggregate rows [T]
- 1.3.4 Pivot, unpivot, and transpose data [T]
- 1.3.5 Convert semi-structured data to a table [T: e.g. JSON from an API]
- 1.3.6 Create fact tables and dimension tables [T]
- 1.3.7 Identify when to use reference or duplicate queries and the resulting impact [T plus written explanation]
- 1.3.8 Merge and append queries [T]
- 1.3.9 Identify and create appropriate keys for relationships [T]
- 1.3.10 Configure data loading for queries [T: enableLoad / staging queries]

## 2 Model the data (25–30%)
(The page marks this heading as an h4, not an h3. That is a markup quirk only.)

**2.1 Design and implement a data model**
- 2.1.1 Configure table and column properties [T]
- 2.1.2 Implement role-playing dimensions [T: inactive relationships, or duplicate date tables]
- 2.1.3 Define a relationship's cardinality and cross-filter direction [T]
- 2.1.4 Create a common date table [T]
- 2.1.5 Identify use cases for calculated columns and calculated tables [T plus explanation]

**2.2 Create model calculations by using DAX**
- 2.2.1 Create single aggregation measures [T]
- 2.2.2 Use the CALCULATE function [T]
- 2.2.3 Implement time intelligence measures [T]
- 2.2.4 Use basic statistical functions [T]
- 2.2.5 Create semi-additive measures [T: e.g. an open-backlog balance]
- 2.2.6 Create a measure by using quick measures [D: a UI feature; its output DAX is T]
- 2.2.7 Create calculated tables or columns [T]
- 2.2.8 Create calculation groups [T: calculationGroup in TMDL]

**2.3 Optimize model performance**
- 2.3.1 Improve performance by identifying and removing unnecessary rows and columns [T]
- 2.3.2 Identify poorly performing measures, relationships, and visuals by using Performance Analyzer and DAX query view [D: Performance Analyzer and DAX query view are Desktop tools; DAX queries can be saved as text]
- 2.3.3 Improve performance by reducing granularity [T]

## 3 Visualize and analyze the data (25–30%)
**3.1 Create reports**
- 3.1.1 Select an appropriate visual [T in the PBIR report definition / D]
- 3.1.2 Format and configure visuals [T/D]
- 3.1.3 Create a narrative visual with Copilot [C: Copilot mode needs F2+/P1; Custom mode needs no Copilot]
- 3.1.4 Apply and customize a theme [T: theme JSON]
- 3.1.5 Apply conditional formatting [T/D]
- 3.1.6 Apply slicing and filtering [T/D]
- 3.1.7 Use Copilot to create a new report page [C]
- 3.1.8 Use Copilot to suggest content for a new report page [C]
- 3.1.9 Configure the report page [T/D]
- 3.1.10 Choose when to use a paginated report [explanation; building one needs Report Builder, which is Windows-only, or the Service]
- 3.1.11 Create visual calculations by using DAX [T in visual definition / D]

**3.2 Enhance reports for usability and storytelling**
- 3.2.1 Configure bookmarks [D mostly]
- 3.2.2 Create custom tooltips [D; tooltip page is T]
- 3.2.3 Edit and configure interactions between visuals [D]
- 3.2.4 Configure navigation for a report [D]
- 3.2.5 Apply sorting to visuals [T/D; sort-by-column is T in TMDL]
- 3.2.6 Configure sync slicers [D]
- 3.2.7 Group and layer visuals by using the Selection pane [D]
- 3.2.8 Configure drillthrough navigation, including pages, filters, and buttons [D]
- 3.2.9 Configure export settings [D/S]
- 3.2.10 Design reports for mobile devices [D]
- 3.2.11 Enable personalization in a report, including personalized visuals [D/S]
- 3.2.12 Design and configure Power BI reports for accessibility [D: alt text, tab order, contrast]
- 3.2.13 Configure automatic page refresh [D; needs DirectQuery, and some intervals need capacity]

**3.3 Identify patterns and trends**
- 3.3.1 Use the Analyze feature in Power BI [D: "Explain the increase/decrease"]
- 3.3.2 Use grouping, binning, and clustering [T for groups/bins; clustering is D]
- 3.3.3 Use AI visuals [D: Key influencers, Decomposition tree; they run in Desktop with no capacity]
- 3.3.4 Use reference lines, error bars, and forecasting [D: Analytics pane]
- 3.3.5 Detect outliers and anomalies [D: line-chart anomaly detection runs in Desktop/Service without capacity]
- 3.3.6 Use Copilot to summarize the underlying semantic model [C]

## 4 Manage and secure Power BI (15–20%)
**4.1 Create and manage workspaces and assets**
- 4.1.1 Create and configure a workspace [S]
- 4.1.2 Configure and update an app [S]
- 4.1.3 Publish, import, or update items in a workspace [S]
- 4.1.4 Create dashboards [S]
- 4.1.5 Choose a distribution method [explanation / S]
- 4.1.6 Configure subscriptions and data alerts [S]
- 4.1.7 Promote or certify Power BI content [S]
- 4.1.8 Identify when a gateway is required [explanation; relevant to a local SQLite source, which would need a gateway for Service refresh]
- 4.1.9 Configure a semantic model scheduled refresh [S]

**4.2 Secure and govern Power BI items**
- 4.2.1 Assign workspace roles [S]
- 4.2.2 Configure item-level access [S]
- 4.2.3 Configure access to semantic models [S]
- 4.2.4 Implement row-level security roles [T: roles in TMDL with DAX filters; testing with "View as" is D]
- 4.2.5 Configure row-level security group membership [S]
- 4.2.6 Apply sensitivity labels [S; needs Microsoft Purview in the tenant]

Counts: 17 + 16 + 30 + 15 = 78 skills.

## Change history (from my diffs of archived versions)
**Change log shown on the page (prior to vs as of April 20, 2026):**
- Get or connect to data: Minor
- Enhance reports for usability and storytelling: Minor
- Create and manage workspaces and assets: Minor
- Everything else: No change

**April 20, 2026:** exact wording changes, from diffing the 2026-03-03 snapshot against the live page:
- 1.1.3: "Choose between DirectQuery and Import" became "Choose between **DirectLake**, DirectQuery, and Import". This is the only Fabric-specific term in the whole outline.
- 3.2.8: "Configure drill through navigation" became "Configure drillthrough navigation, **including pages, filters, and buttons**".
- 3.2.11: "Enable personalized visuals in a report" became "Enable **personalization in a report, including** personalized visuals".
- 4.1.2: "Configure and update a **workspace** app" became "Configure and update **an** app".

**January 15, 2026** (Create reports = Major; Identify patterns and trends = Minor). Added:
- 3.1.3 "Create a narrative visual with Copilot"
- 3.1.7 "Use Copilot to create a new report page"
- 3.1.8 "Use Copilot to suggest content for a new report page"
- 3.3.6 "Use Copilot to summarize the underlying semantic model"

**April 21, 2025:** a minor wording change only ("drillthrough" became "drill through"; April 2026 changed it back).

**October 21, 2024 (major rewrite)** compared with the April 23, 2024 outline:
- **Groups:** "Deploy and maintain items" was renamed "Manage and secure Power BI". "Manage semantic models" was **deleted**. "Secure and govern Power BI items" is **new**. RLS roles moved from the Model group to Secure and govern. Automatic page refresh moved to Enhance reports.
- **Added:**
  - DAX query view (in 2.3.2)
  - Create calculation groups
  - Create visual calculations by using DAX
  - Pivot, unpivot, and transpose
  - Convert semi-structured data to a table
  - Group and aggregate rows
  - Create fact tables and dimension tables (replacing "Design a star schema")
  - Identify use cases for calculated columns and calculated tables
  - Improve performance by reducing granularity
  - Create and modify parameters (was "Change the value in a parameter")
- **Removed:**
  - Incorporate the Q&A feature in a report
  - Create and share scorecards and metrics
  - Use a custom visual
  - Use the Analyze in Excel feature
  - Identify implicit measures and replace with explicit measures
  - Dual mode (from the storage-mode choice)
  - Improve performance by choosing optimal data types / by summarizing data
  - Manage global options for files
  - Data source locations (from 1.1.2)

**Terms that never appear in the outline:** Fabric, OneLake, lakehouse, PBIP, TMDL, Git integration, deployment pipelines, dataflows, Python/R visuals.

## Platform facts that affect an honest Mac-only build
- **Copilot needs paid capacity.** "Paid Fabric capacity (F2 or higher) or Power BI Premium (P1 or higher). Trial capacities and free SKUs aren't supported." A Pro or PPU licence alone isn't sufficient. In Desktop you need write access to a workspace on such capacity. Doc ms.date 2026-08-24: https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction
  - Consequence: skills 3.1.3, 3.1.7, 3.1.8 and 3.3.6 cannot be shown on a free or trial setup.
  - The Narrative visual's **Custom mode** (dynamic values, no Copilot) is available: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-smart-narrative
- **AI visuals.** The docs' "AI-powered visuals" group lists Decomposition tree, Key influencers, Smart narrative and Anomaly detection (https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualizations-overview).
  - The same page says: "The Q&A visual is scheduled for deprecation in December 2026."
  - A September 14, 2026 republished Fabric Community post says: "Beginning in February 2027, Q&A will no longer work in Power BI" (https://msbitutor.blogspot.com/2026/09/power-bi-q-retirement-reminder-february.html; the original community.fabric.microsoft.com post returned 403).
  - Do not build on the Q&A visual.
- **Anomaly detection** works in Desktop and the Service, with limits (https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-anomaly-detection):
  - Line charts with a time-series axis only.
  - At least 4 data points.
  - No legend, multiple values or secondary values.
  - Cannot be combined with Forecast, Min, Max, Average, Median or Percentile lines.
  - It gives explanations using configurable "Explain by" fields. Daily 311 request counts by borough or complaint type fit these limits.
- **Name confusion.** The exam code has not changed. The exam title and the certification title are simply different (https://learn.microsoft.com/en-us/answers/questions/5823623/name-of-pl300-is-changed).

## Sources
- Live study guide: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300
- Wayback snapshots used for the diffs (each URL is followed by /https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/pl-300):
  - http://web.archive.org/web/20260719183800 (identical to live)
  - http://web.archive.org/web/20260415210613 (April 20, 2026 outline)
  - http://web.archive.org/web/20260303130039 (January 15, 2026 outline)
  - http://web.archive.org/web/20251221144344 (January 15, 2026 outline)
  - http://web.archive.org/web/20250418190442 (April 21, 2025 outline)
  - http://web.archive.org/web/20241221191215 (October 21, 2024 outline and its change log)
  - http://web.archive.org/web/20240426174112 (April 23, 2024 outline)
- Certification page: https://learn.microsoft.com/en-us/credentials/certifications/power-bi-data-analyst-associate/
- Copilot requirements: https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction
- Visual types / Q&A deprecation: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualizations-overview
- Smart narrative: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-smart-narrative
- Anomaly detection: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-anomaly-detection
- Q&A retirement extension (secondary): https://msbitutor.blogspot.com/2026/09/power-bi-q-retirement-reminder-february.html

Working copies of the downloaded pages and extracted text are in <scratch folder> (pl300.html, v_*.txt).


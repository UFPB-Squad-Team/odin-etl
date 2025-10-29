Technical Report - Geocoding Tools

This report presents a survey and comparative analysis of geocoding APIs and libraries, considering open-source, paid, and free options. The goal is to identify the most suitable solutions for projects involving geographic location and spatial data integration, such as geocoding schools in the state of Paraíba.

# Survey of Geocoding Tools and APIs

To meet the need for a sustainable solution, several geocoding tools were identified, divided between Open-Source / Self-Hostable solutions and Commercial / Freemium solutions. Among the open-source options are: **Nominatim (OpenStreetMap)**, a widely used public software and service ideal for high-volume requests without licensing costs; **Pelias**, an open-source geocoder based on Elasticsearch, excellent for self-hosting and full control of data; and **Photon**, maintained by Komoot and based on OpenStreetMap data, known for its high search speed. Commercial options include the **Google Maps Geocoding API** (reference for high accuracy, but with a pay-as-you-go model), **Mapbox Geocoding API** (robust commercial alternative and direct competitor to Google, with limited free plans), **OpenCage API** (commercial service built on open data, with paid plans and a predictable free tier), and **LocationIQ and MapQuest** (low-cost commercial alternatives that are easy to integrate, based on OpenStreetMap, representing a hybrid low-cost solution).

# Comparative Matrix of Tools

| **Provider**         | **Type**    | **Cost**                      | **Accuracy/Coverage**        | **Limits/Quota**           | **Complexity**   |     |
| -------------------- | ----------- | ----------------------------- | ---------------------------- | -------------------------- | ---------------- | --- |
| Nominatim (OSM)      | Open-source | Free (public usage restrictions) | Good, depends on OSM         | Public usage limits        | Low              |     |
| Pelias               | Open-source | Free (infrastructure cost)    | Depends on imported data     | No limits (self-host)      | High             |     |
| Photon               | Open-source | Free (infrastructure cost)    | Good for search and typeahead| No limits (self-host)      | Medium           |     |
| Google Maps          | Commercial  | Pay-per-use                   | Excellent global accuracy    | High paid limits           | Low              |     |
| Mapbox               | Commercial  | Freemium                      | Very good                   | Batch and reasonable limits| Low–Medium       |     |
| OpenCage             | Commercial  | Monthly plans                 | Good, combines multiple sources | Moderate limits         | Low              |     |
| LocationIQ / MapQuest| Commercial  | Free tier + paid plans        | Good                        | Generous limits            | Low              |     |

# Drawbacks of Adopting Each API

**Nominatim (OSM)** has the main difficulty of strict public usage restrictions, limiting the number of requests and causing unstable performance under high demand. **Pelias**, while open-source and scalable, requires dedicated infrastructure and complex configuration with Elasticsearch, plus continuous maintenance of local data, which raises technical deployment costs. **Photon**, also based on OpenStreetMap data, requires hosting and regular database updates to maintain accuracy, which implies constant operational effort. The **Google Maps Geocoding API** is the most precise and easiest to use, but faces the greatest obstacle in high per-request cost and the legal risk of violating Terms of Service by attempting to circumvent the free usage limit with multiple accounts. **Mapbox** offers good accuracy and a modern interface, but its free tier is limited and costs grow quickly as usage increases. **OpenCage** combines various open sources and is easy to integrate, but shows lower accuracy in rural areas and has fixed monthly costs that may make it unfeasible for low-budget projects. Finally, **LocationIQ / MapQuest** is a low-cost commercial option with generous limits, but depends on stable connectivity and can suffer performance degradation during usage peaks, which may compromise reliability under heavy load.

The Google Geocoding API Dilemma

The preference for Google's API is technically justified by its effectiveness and simplicity of use and by the progress already achieved by the team. The technical infeasibility of switching APIs is evident given the reengineering cost and learning curve of an alternative.

However, this dependency conflicts with a critical cost barrier: the free usage limit of $200 (one-time fixed credit) was quickly exhausted just considering the demand from public schools, indicating the current model is unviable for the full regional scope.

Compliance and Sustainability Risk

To bypass the limit, the proposed strategy of creating multiple user accounts to fragment the free credit entails a serious compliance risk. This tactic violates Google's Terms of Service (ToS), generating complexity in managing multiple API keys and, more seriously, exposing the project to legal vulnerability.

The main conflict in this hypothetical debate is that current technical efficiency threatens the ODIN project's sustainability and commercial future. Potential ToS violations could prevent contract signing and sale of the application to interested organizations, turning a technically viable decision into a strategic and legal obstacle to scalability and long-term success.

The debate therefore centers on prioritizing: (A) maintaining the Google API, accepting the compliance risk and future commercial infeasibility, or (B) urgently pursuing an alternative geocoder with predictable costs and clear terms of use, ensuring ODIN’s longevity and contractability.

Keywords: ODIN Project, Geocoding, Google API, Compliance Risk, Sustainability, Public Policy.

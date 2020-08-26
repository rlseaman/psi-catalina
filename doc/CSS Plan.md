# PDS/SBN Catalina Sky Survey Archive Plan April 11, 2017

## 1. Introduction

### 1.1. Purpose and scope

This PDS/SBN Catalina Sky Survey (CSS) Archive Plan describes the proposed plan and schedule for generation, validation and transfer of CSS archival data and documentation to the NASA Planetary Data System archives at the Small Bodies Node at PSI. This plan has been developed with input from the Catalina Sky Survey and the PDS Small Bodies Node.

### 1.2. Applicable Documents

* Planetary Data System Standards Reference, Version 1.7.0, JPL D-7669, Part 2, Sept. 15, 2016.
* Data Provider's Handbook: Archiving Guide to the PDS4 Data Standards, Version 1.4.1, Feb. 23, 2016.
* PDS4 Concepts, Version 1.7.0, Sept. 15, 2016.
* SBN Archive Pipeline Review Guidelines, Mar. 2, 2016.
* any others?

## 2. The Catalina Sky Survey Project 

### 2.1. Overview

CSS is a ground based telescopic survey project which seeks to discover Near-Earth Objects (NEOs) that potentially could impact Earth. CSS has been in operation since 2003 and is currently funded under a NASA NEOO grant (“The Catalina Sky Survey for Near-Earth Objects”) which includes the requirement to make the CSS archives available to the public.

The current phase of the CSS calls for reprocessing archival data with an improved pipeline which will allow new measurements of previously undetected asteroids, as well as improved measurements of previously reported objects. We will work with the Minor Planet Center to replace CSS observations in their catalog with improved measurements under the newly adopted IAU 2015 astrometry standard, potentially improving the orbits of a large fraction of the nearly 700,000 asteroids currently in the MPC catalog, both main-belt asteroids and NEOs alike. At the end of the proposed work period, the CSS data archive will be uniform, rigorously vetted, and beginning ingestion into a public scientific archive, namely the Small Bodies Node of NASA’s Planetary Data System (PDS).

### 2.2. Telescopes and instruments

Data from the Catalina Sky Survey has resulted from three predominantly survey discovery telescopes, two in Arizona and one in Australia, and one astrometric follow-up telescope in Arizona. We are actively seeking access to additional telescopes and will negotiate PDS support for any new data streams as appropriate in the future. Figure 1 summarizes the past and current telescopes and cameras.

| Telescope                       | MPC Code | Location                 | Aperture f/no | Field of  View | Pixel scale arcsec/pix | 50% limiting mag. | Coverage/ 10 hr | Dates of Operation |
|---------------------------------|----------|--------------------------|---------------|----------------|------------------------|-------------------|-----------------|--------------------|
| Bigelow Schmidt                 | 703      | Mt. Bigelow, Arizona     | 0.7-m f/1.8   | 8.13  deg^2    | 2.5"                   | ~19.7 V           | 1,500 deg^2     | 2003 - present     |
| Mt. Lemmon Prime Focus          | G96      | Mt. Lemmon, Arizona      | 1.5-m f/2.0   | 1.22 deg^2     | 1.0"                   | ~21.3 V           | 220 deg^2       | 2004 - present     |
| Uppsala Schmidt                 | E12      | Siding Spring, Australia | 0.5-m f/3.0   | 4.19 deg^2     | 1.8"                   | ~19.3 V           | 700 deg^2       | 2004 - 2013        |
| Mt. Lemmon 1-meter              | I52      | Mt. Lemmon, Arizona      | 1.0-m f/2.6   | 0.25 deg^2     | 1.0"                   | ~21.6 V           | 60 deg^2        | 2014 - present     |
| Upgraded Bigelow Schmidt        | 703      | Mt. Bigelow, Arizona     | 0.7-m f/1.8   | 19.36 deg^2    | 1.5"                   | ~19.7 V           | 4,000 deg^2     | 2016+              |
| Upgraded Mt. Lemmon Prime Focus | G96      | Mt. Lemmon, Arizona      | 1.5-m f/1.6   | 5.10 deg^2     | 0.8"                   | ~21.3 V           | 1,000 deg^2     | 2016+              |


**Figure 1** – details for CSS telescopes and cameras


### 2.3 Data Characteristics Overview

Data from all configurations has remained very similar, though has slowly evolved over the years. Commissioning of the upgraded 10k cameras at the Bigelow and Mt. Lemmon sites has coincided with a period of rapid evolution. The first stages of the archive project will include updating old data holdings to meet current CSS data standards.

The CSS archive goes back to 2003, containing nearly 3 million images across the four telescopes. As of January 2017, this amounts to approximately 37.7 terabytes: 15.9 TB from the Schmidt telescope on Mount Bigelow, 12.2 TB from the Mount Lemmon 1.5m, 8.3 TB from the Siding Spring Schmidt, and 0.2 TB from the Lemmon 1.0m. There are about 1.1 TB of additional data products.

Converting this to an archival data volume is complicated by the lossy compression algorithm that was originally used. Our current data are losslessly compressed using FITS tile compression and data will be prepared for ingest into PDS by recompressing the data using FPACK(1). It is anticipated that the resulting files will remain roughly the same size.


1: http://heasarc.gsfc.nasa.gov/FTP/software/fitsio/c/docs/fpackguide.pdf

Newly acquired losslessly compressed images are larger than lossy compressed versions.
 
These holdings correspond to about 15 million files of all types, including source extractor catalogs, candidate asteroid detections, and final astrometric submissions, among several other kinds. It is possible that CSS will add, or less likely remove, some classes of files from the data products. These files are generated per-image, per-field, per- asteroid, and so forth.

The recent upgrade from 4k-square to 10k-square cameras will increase all future data volumes, though again the precise impact is difficult to estimate since one of the two cameras is operating binned 2x2. During commissioning we are also investigating different regimes of exposure times, and the underlying cadence has changed with the more rapid readout of the new cameras, balanced by the longer slews and a new TCS (telescope control system). A large impact will be the anticipated inclusion of raw camera images in the archival holdings. An increase by a factor of ten in nightly data volumes would not be unlikely.

A conservative, but very rough, estimate for annual CSS data volumes beginning in 2017 is around 40 TB (compressed). A more accurate (and probably smaller) estimate will be possible about halfway through 2017.

## 3. The CSS Archive Contents 

### 3.1. Inventory of data products

CSS data products are generated from multiple imaging sequences of standard survey fields indexed by right ascension and declination. This include targeted follow-up fields with non-standard RA and Dec, but also varying exposure time and other settings from the survey defaults. Generally our cameras are optical white light, though filters are possible for some configurations. The images are FITS format and the headers include a wide variety of the typical astronomical keywords.

Historically CSS has used the lossy H-compress algorithm, but all data submitted for SBN ingest will be in FITS tile-compressed (FPACK) format, lossless for new data and preserving the available entropy for previously lossy images. The original lossy compression was, in most cases, prudently chosen and the images are useful for all scientific purposes. A relatively small set of data from the Siding Spring Survey have been compromised and the inclusion of these images is TBD. Some small fraction of fields from all telescopes have missing images and we will generally submit these data as of historical and perhaps scientific interest in any event.

CSS has heretofore archived only pipeline-reduced data products. Raw data may also be submitted in the future.

CSS data products include non-image text and binary data products as described below. Individual files may or may not be gzip compressed (or other compression as later determined by the peer committee). SBN should be prepared to receive and ingest both compressed and uncompressed examples of all data products. The compression as stored in PDS is for discussion by the peer committee. Which is to say that CSS expects to deliver compressed data for instances of the larger data products (e.g., source extractor catalogs), and uncompressed data for small files (to simplify both internal and external access), but this is an example of where logistics might vary.

| UTDate   | Narch | +Nsext | +Ne | +Nd | +Nm  | +Nh | +Nr | +Oth | =Ntot  | Nfield | Disk (mb) |
|----------|-------|--------|-----|-----|------|-----|-----|------|--------|--------|-----------|
| 20170104 | 200   | 200    | 50  | 50  | 43   | 50  | 50  | 1500 | 2143   | 50     | 8073      |
| 20170105 | 576   | 571    | 144 | 144 | 134  | 144 | 144 | 4134 | 5991   | 144    | 28087     |
| 20170106 | 72    | 72     | 18  | 18  | 19   | 18  | 18  | 531  | 766    | 18     | 3215      |
| 20170107 | 932   | 930    | 233 | 233 | 223  | 233 | 233 | 6576 | 9593   | 233    | 42817     |
| 20170108 | 308   | 279    | 70  | 70  | 60   | 70  | 70  | 2128 | 3055   | 77     | 14300     |
| 20170109 | 848   | 832    | 209 | 209 | 197  | 209 | 209 | 5977 | 8690   | 212    | 34593     |
| 20170119 | 468   | 467    | 117 | 117 | 115  | 117 | 117 | 3355 | 4873   | 117    | 19831     |
| 20170126 | 788   | 784    | 197 | 197 | 192  | 197 | 197 | 5610 | 8162   | 197    | 32692     |
| 20170127 | 704   | 698    | 176 | 175 | 169  | 176 | 176 | 5126 | 7401   | 176    | 30209     |
| 20170128 | 784   | 780    | 196 | 196 | 193  | 196 | 196 | 5572 | 8113   | 196    | 31454     |
| 20170129 | 904   | 898    | 226 | 226 | 199  | 226 | 226 | 6321 | 9226   | 226    | 38486     |
| 20170130 | 796   | 794    | 199 | 199 | 192  | 199 | 199 | 5709 | 8287   | 199    | 35991     |
| 20170131 | 840   | 838    | 210 | 210 | 206  | 210 | 210 | 5973 | 8697   | 210    | 33978     |
| 20170201 | 800   | 799    | 200 | 200 | 196  | 200 | 199 | 5706 | 8300   | 200    | 35354     |
| 20170202 | 764   | 761    | 191 | 191 | 167  | 191 | 191 | 5421 | 7877   | 191    | 33423     |
| 20170203 | 684   | 681    | 171 | 171 | 99   | 171 | 171 | 4841 | 6989   | 171    | 30263     |
| 20170204 | 532   | 529    | 132 | 132 | 130  | 132 | 132 | 3791 | 5510   | 133    | 23000     |
|          |       |        |     |     |      |     |     |      |        |        |           |
| Total    | 11000 | 10913  | ->  | ->  | 2739 | <-  | <-  |      | 113673 | 2750   | 464.62GB  |

**Figure 2** - inventory of G96 data products for first month of 2017. Narch is the number of FITS images acquired. These are typically in per-field sequences of four exposures. Other pipeline data products are generally grouped one-per-image or one-per-field. Astrometric output is clustered per- NEO, with a single list of incidental MBA observations.

CSS data products fall into several classes, and instances of files in each class generally scale with 1) the number of camera exposures, 2) the number of survey or follow-up fields, or 3) the number of NEOs per night. Calibrations and such files (e.g., flat fields) may be present in arbitrary numbers of a few dozen per night.

| Product            | Type  | Ext  | Description                                  |
|--------------------|-------|------|----------------------------------------------|
| Raw exp            | image | fits | Raw camera exposure                          |
| Proc exp           | image | arch | Pipeline processed camera exposure           |
| Bright sources     | table | sexb | Sextractor program output (binary)           |
| Deep sources       | table | sext | Sextractor program output (text)             |
| Difference sources | table | iext | Sources detected through image differencing  |
| Field catalog      | table | strp | UCAC4 catalog info for field with photometry |
| Field matches      | table | strm | Sources matching catalog entries             |
| SCAMP params       | xml   | xmls | Astrometric parameters                       |
| SCAMP output       | table | scmp | Astrometric results                          |

Data products whose numbers scale with survey or follow-up fields:

| Product          | Type  | Ext   | Description                                                    |
|------------------|-------|-------|----------------------------------------------------------------|
| Difference image | image | csub  | Difference field (stars subtracted leaving moving objects)     |
| Ephemeris        | table | ephem | Ephemerides of known asteroids in field at time of observation |
| MTD objects      | table | mtds  | Scored moving transient detections from sext / iext files      |
| Filtered objects | table | mtdf  | Filtered detections (linked to ephemerides and with digest2)   |
| Detections       | table | dets  | Ranked candidate asteroid detections                           |
| Hits             | table | hits  | Automatically associated observations                          |
| Rejects          | table | rjct  | Candidates rejected by human observer                          |
| MPC Batch        | table | mpcd  | Astrometry for non-NEOs, to be batch submitted to MPC          |

Data products related to workflow or per-NEO discovery:

| Product           | Type    | Ext        | Description                                  |
|-------------------|---------|------------|----------------------------------------------|
| Parameters        | text    | param      | Workflow parameter input                     |
| JSON              | json    | json       | JSON configuration files                     |
| Logs              | text    | log        | Log files                                    |
| MPC Reports       | mpc1992 | mrpt       | Submitted MPC astrometric reports            |
| NEOS              | table   | neos       | Per-field NEOs (if any)                      |
| Failed astrometry | table   | fail       | Per-field failed astrometry                  |
| Pass1 images      | image   | pass1      | Special case images (infrequent)             |
| Follow-up         | table   | followup   | Follow-up field metadata                     |
| Pointing          | text    | point      | Auto-generated end-of-night observing report |
| Flats             | image   | flat       | CCD flat fields used tonight                 |
| Astrometry        | table   | ast        | Astrometry work file                         |
| Signature         | text    | signature  | MD5 signatures for file manifest             |
| User              | table   | userfields | User field metadata                          |

Nightly data products:

| Product             | Type  | Ext  | Description |
|---------------------|-------|------|-------------|
| Survey planner info | text  | txt  |             |
| Auto-pointing model | image | fits |             |
| Sky coverage        | text  | cov  |             |
| SVN versions        | text  | txt  |             |
| End-of-night NEOs   | table | neos |             |



### 3.2. Inventory of documents

These documents will be included in the archive. Documents can be either PDF/A or plain text.

* bundle description - an overall description of the contents and structure of the bundle, including data and documents.
* instrument descriptions for each instrument (camera) for which there is data.
* CSS project description - can be a reference to a published paper.
* processing document (what is done to get from raw to cal)
* pipeline configuration management document (not to be archived, this is needed for the pipeline review)
* references list - papers cited in the bundle documentation or labels
* other documentation such as log files, qe curves for cameras, etc., TBD.

### 3.3. Archive structure, such as grouping of products into collections and bundles.


Refer explicitly to PDS4 standards and cite PDS4 standards reference as appropriate. Specify 
which version of the PDS information model will be used. [Given the data product inventory Carol 
will suggest a recommended structure and we can discuss and modify as needed.]

(see <https://sbn.psi.edu/css/CSS_Bundle_Design.xlsx>)

### 3.4. Detailed collection and bundle contents (probably in a table). 

[Carol can supply once we have 3.1-3.3 above.]

## 4. Archive Generation, Validation, and Transfer

### 4.1. Roles and Responsibilities

CSS will be responsible for these aspects of the archiving process:
* Set up a configuration-controlled data pipeline for delivery of archive-ready PDS4-compliant CSS data products and labels to SBN.
* Produce a configuration control document describing the pipeline and its control process, in compliance with PDS requirements and the SBN pipeline review guidelines.
* Produce required documentation, including instrument, data processing, and project documentation, for inclusion in the CSS archive.
* Participate in the PDS peer review of the pipeline.
* Resolve liens from the PDS peer review.
* Participate in the configuration control board.
* Work with SBN to design a transfer mechanism for the data deliveries.
* Deliver existing CSS data and continue to deliver new data to SBN by means of the pipeline and transfer mechanism.
* Participate in additional PDS peer review and liens resolution as needed to accommodate new data products or other major changes in the pipeline. SBN will be responsible for these aspects of the archiving process:
* Assist in designing PDS4-compliant formats and labels for the CSS data products.
* Work with CSS to design a transfer mechanism for the data deliveries.
* Assist in preparation of the configuration control document.
* Conduct external peer review of the pipeline.
* Assist CSS in resolving the liens from the peer review.
* Participate in the configuration control board to determine when changes to the pipeline are large enough to require additional internal or external review.
* Maintain an online repository of CSS science data archives, allowing publicaccess to the data.
* Deliver all archived CSS data to NSSDCA for deep archive.

### 4.2. Archive pipeline

The CSS workflow is focused on the discovery of Near Earth Objects (asteroids and comets). As a matter of course CSS also discovers Main Belt Asteroids and more distant objects (Jupiter Trojans, etc.), but CSS is tuned for nearby and sometimes rapidly moving objects. Indeed, CSS data also includes astrometry and streaks from artificial spacecraft and their geocentric orbital debris.

As with any mission whose data are archived in PDS, the primary responsibility of CSS is to our own mission, and this includes a pipeline that will remain optimized for NEO discoveries. Archive use cases must fit into this framework with minimal impact. That said, we recognize the responsibility to address the goals of the new archive head-on.

Roughly speaking, the CSS pipeline is a TCL and C-based data-driven state machine. Transitions from state-to-state are triggered internally as spawned processes complete each step, but are also triggered on the pipeline input side by the queue-managed data acquisition process filling the hopper with data roughly every 45s all night long. And transitions may also be triggered by the intervention of the human observer, though these are generally broader decisions (e.g., “clouds coming in”) regarding the pipeline itself.

All CSS pipeline processing occurs in real-time on servers co-located with our telescopes. This will include features added in support of PDS-ingest. We expect to create PDS-4 data product labels during each night, perhaps including a pre-processing step (e.g., to set parameters specific to each telescope and observer), as well as a post- processing step (an initial validation of the list of data and state of processing).

It is not atypical for CSS telescopes to be placed into a state of lightning shutdown, often on very short notice. This includes the pipeline servers. Pipeline restart procedures will include a method to ensure that calibration, configuration, image data and metadata are not lost. Any such shutdown will delay submission to the PDS-SBN, but should not impact the quality of the product.

The PDS-SBN does not place any constraints on where the data is processed or from where it is transmitted. The initial mountaintop validation may reveal issues and it is a TBD whether these will be addressed on the mountain or at CSS HQ on the University of Arizona campus. The precise procedures are also TBD and may involve rerunning all or part of the CSS pipeline. It is likely that most such exception handling, if not at the
telescope, will occur at LPL’s Kuiper Space Sciences building where copy A of the internal CSS archive resides. Only after resolving issues will data be transferred to copy B at the campus UITS data center (see below).

Later corrections to data sets might conceivably originate with either copy A or copy B and then backfill to the other copy, but these procedures are TBD. Whenever revisions occur, either same-night or long after, CSS will validate the resulting data sets against PDS-4 standards. Resubmission, should it occur, will be subject to review by the peer committee.

The archive reprocessing data set can loosely be referred to as copy C, also resident on CSS servers at UITS. It is anticipated that data preparation steps (e.g., conversion to FPACK and updating header keywords to current CSS standards) will occur in-place on copy C. The updated per-telescope per-night data sets will be passed through an instance of the current CSS pipeline running on the UITS servers, also creating the PDS-4 labels and related data product lists, etc. These legacy batch data sets will be transfers to SBN as described in section 4.4 below.

### 4.3. Peer review

The PDS external pipeline review serves to validate several aspects of the data prior to archiving: 1) The design of the data products, labels, metadata, and documentation are consistent with PDS standards and support the scientific usefulness of the archive, 2) The pipeline is capable of producing the ongoing archive deliveries correctly, 3) The configuration control of the pipeline is capable of managing changes to the pipeline in a manner consistent with PDS requirements.

The output of the pipeline submitted for review should consist of a complete PDS- compliant archive bundle containing sample products representing all product types to be archived, and representing all instruments producing data. The bundle should also include all documents that will accompany the archive. The configuration control document will also be submitted for the review.

SBN will select external reviewers (not involved with either SBN or CSS) and who are active researchers in planetary science fields relating to the CSS data products. CSS is encouraged to suggest reviewers. In addition, the review panel includes PDS personnel who confirm compliance with PDS archiving standards. CSS representatives will participate in the review meeting to assist in identifying workable solutions to any concerns found by the panel.

The pipeline review may result in liens on the pipeline, the configuration control, the documents, and/or the product or label design. CSS will be responsible for resolving the liens with the help of SBN. After liens resolution is completed and confirmed by SBN and CSS, ongoing deliveries from the pipeline may be archived without further external review.

#### 4.3.1 Changes within the CSS pipeline

It is expected that changes will occur to the CSS pipeline. A configuration control board (CCB) will monitor changes to the pipeline, and the SBN representative on the CCB will determine when changes to the pipeline (such as addition of a new product type or a redesign of products or labels) are large enough to require additional internal or external review.
When changes are suggested, or if time critical, implemented, a notification will generated and send to the CCB. The notification will include:

* Date
* Scope of impact
* Range of dates to which it applies Expected version number
* Will it require reprocessing of old data

The PDS representative on the CCB will review the notification and confer with the CSS as to the impact of the change. The following is a list of potential items that would trigger a notification. Resolution of these issues by the CCB can be accomplished by direct approval, approval upon receipt of regression testing report, internal PDS-review or external PDS-review.
Change/addition of camera/CCD/telescope Change in FITS keywords
Updated calibration technique and algorithm Software changes

### 4.4. Archive transfer to PDS
Archive transfers from CSS to SBN fall into two general classes: 

1. nightly near-real- time transfers, and 
2. the batch transfer of reprocessed archival data sets. 

Current thinking is to commission these two modes in that order. Once the pipeline has been certified by the PDS Review Committee, CSS will begin nightly transfers from their telescopes. LPL and PSI personnel will coordinate to tune the infrastructure to a level of efficiency deemed acceptable to both parties, likely in the range of latencies on the scale of hours to days from end-of-night to availability in PDS.

Once nightly transfers are happening smoothly from all CSS telescopes, the focus will shift to initial batch transfers, likely on the scale of one lunation’s (month’s) observations from a single telescope. Batch and nightly transfers will be scheduled concurrently and must not be allowed to interfere one with the other. Batch reprocessing will proceed at a pace permitted by the CSS archive servers. Nightly ingest will continue indefinitely as procedures are tested to handle special cases and user requests.

Catalina personnel are currently working on the details of the internal procedures outlined below, but the general concepts should remain as described:

1. All external data transfers will originate from CSS servers at the campus UITS data center.
2. Standard linux protocols will be used for transfers, e.g., rsync for bulk data and perhaps curl for individual files. If PSI and LPL agree, other options are possible.
3. CSS has historically been open to enabling real-time transfers, e.g., to the Catalina Real-time Transient Survey (CRTS) at Caltech, however, we don’t currently anticipate SBN ingest need operate in real-time.
4. Step 1 - data will be transferred during non-standard office hours (M-F 6pm until 7am and all day Saturday and Sunday), or at a restricted data rate to avoid network saturation of either facility.
5. Step two - transfer validation using standard tools such as a list of MD5 checksums.
6. Step three - PSI to trigger PDS ingest on the complete nightly data set.
7. State transitions between each step will be mediated with some simple technique such as a semaphore.
8. The initial action during PDS ingest will be a semantic validation replicating the CSS archive pipeline. Issues detected will generate exception handling between CSS and PSI. (Presumably there will also be a class of server or SBN storage exceptions that are purely internal to PSI.)
9. When possible straightforward exceptions will permit automated recovery, and this capability will grow as personnel from both teams become familiar with these data. That does not preclude a general exception for an unhandled circumstance upon which humans will need to manually diagnose and correct the issue.
10. We anticipate that CSS and PSI will develop a toolkit(s) over time to implement the different facilities implied above.
11. Batch transfers of legacy reprocessed data will originate from the same UITS- based server(s) as the nightly data sets. CSS anticipates handling legacy data sets in monthly or larger chunks, and transfers will only occur when each chunk is complete and has been internally vetted by both pipeline procedures and human spot checking.

### 4.5. Schedule [I've just listed some significant milestones without any specific dates yet, but mostly in chronological order. We can work on fleshing this out and assigning estimated dates.]

* CSS completes the data inventory and supplies samples of each data type to SBN.
* SBN validates and approves archival formats for all data types.
* Validated PDS4-compliant label design for all products is completed.
* Documentation set is completed.
* Data transfer mechanism is completed and tested.
* Configuration control document is completed.
* Pipeline is finalized for peer review.
* Peer review of the pipeline is held.
* Liens resolution is completed.
* Data generation, transfer, and archiving of ongoing CSS data is operational.
* All reprocessed past data volumes are generated, transferred to SBN, and archived.

### 4.6. Distribution

Once delivered to the PDS, the CSS archives will be publicly available on-line through the standard PDS registry and search service, as well as via more specialized PDS search and retrieval tools TBD. Data will be available to the public via electronic transfer. All CSS archive products will be transferred to the NSSDCA for deep archive.

### 5. Cognizant Persons
 
| Name             | Affiliation/Role        | email                       |
|------------------|-------------------------|-----------------------------|
| Eric Christensen | CSS PI                  | eric@lpl.arizona.edu        |
| Steve Larson     | CSS Co-I                | slarson@lpl.arizona.edu     |
| Rob Seaman       | CSS data engineer       | seaman@lpl.arizona.edu      |
| Eric Palmer      | SBN/PSI PI              | palmer@psi.edu              |
| Don Davis        | SBN NEO Surveys lead    | drd@psi.edu                 |
| Carol Neese      | SBN archivist           | neese@psi.edu               |
| Jesse Stone      | SBN software specialist | jstone@psi.edu              |
| Richard Chen     | PDS EN data engineer    | richard.l.chen@jpl.nasa.gov |

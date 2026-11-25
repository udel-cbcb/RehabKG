# RehabKD_With_LLM-KG-LDACX_Orchestrating_AI_Models_for_Rehabilitation_Knowledge_Discovery.pdf

pages: 28
sha256: 0ef1f9196aee786c3971a621abe9f3bdf102ba5571a512c8246da98ef4e86eb6

--- page 1 ---
Received 14 November 2025, accepted 12 December 2025, date of publication 18 December 2025,
date of current version 26 December 2025.
Digital Object Identifier 10.1109/ACCESS.2025.3645851
RehabKD With LLM-KG-LDACX: Orchestrating AI
Models for Rehabilitation Knowledge Discovery
WEI ZHANG, ZHIZHONG XING , AND SHAOCHUN CHEN
School of Rehabilitation, Kunming Medical University, Kunming 650500, China
Corresponding author: Shaochun Chen (chenshaochun@kmmu.edu.cn)
This work was supported in part by Yunnan Fundamental Research Projects under Grant 202401AU070071, in part Kunming Medical
University Talent Introduction Research Special Project under Grant 2404, in part by the Xingdian Talent Support Program of Yunnan
Province of China under Grant XDYC-QNRC-2024-185, and in part by the Scientific Research Fund of the Yunnan Provincial Department
of Education under Grant 2024J0337.
ABSTRACT Artificial intelligence (AI), as an emerging scientific paradigm, is pivotal in fostering
interdisciplinary research and driving knowledge discovery. To map the knowledge evolution and
technological integration of AI in rehabilitation science, this study proposes rehabilitation knowledge
discovery (RehabKD), a multi-model collaborative AI framework, and investigates its potential for
exploring literature data, mining insights, and constructing a knowledge graph. Our approach encompasses
three phases: 1) Data Exploration, involving sentiment analysis of titles to assess emotional dynamics,
unsupervised dimensionality reduction of semantic vectors (using manifold learning and variational
autoencoders), and exploratory clustering (e.g., K-Means, HDBSCAN) of the semantic space; 2) Data
Mining, featuring deep mining of community structures in co-occurrence networks and temporal topic
evolution analysis using Latent Dirichlet Allocation (LDA); and 3) Knowledge Discovery, enabled by
our novel large language model – knowledge graph - latent dirichlet allocation and complex network co￾occurrence matrix model (LLM-KG-LDACX). These methods were evaluated with metrics grouped by
objective: sentiment analysis used polarity/subjectivity indices; semantic clustering used Silhouette Score,
Calinski Score, and Davies Score (to compare strategies); complex network community detection used
degree distribution and clustering coefficient (to measure keyword neighborhood features); knowledge
graph construction used accuracy, completeness, connectivity, and redundancy (to compare strategies);
additionally, entity recognition statistics, external validation support, relationship extraction statistics,
external co-occurrence support, and external exact match support served for PubMed external validation
and method comparison. The results demonstrate that our multi-model framework effectively facilitates
rehabilitation knowledge discovery, establishing a ‘‘data-driven → model collaboration → knowledge
graph → disciplinary mapping’’ paradigm. Crucially, without requiring labeled data for training, the LLM￾KG-LDACX model extracted significantly more valid entities and relationships from the target dataset than
supervised benchmarks (biLSTM-CRF, BERT) and an LLM-only baseline, as confirmed by external PubMed
validation. This work provides rehabilitation science with a reusable analytical framework (RehabKD) and
a powerful knowledge engine (LLM-KG-LDACX), offers empirical evidence for AI’s role as a ‘‘scientific
collaborator,’’ and contributes to optimizing research decision-making.
INDEX TERMS Artificial intelligence for sciences, text mining, multi-models collaboration, large language
model, knowledge graph, complex network.
The associate editor coordinating the review of this manuscript and
approving it for publication was Yongming Li .
I. INTRODUCTION
The rapid advancement of artificial intelligence (AI) is
revolutionizing scientific research, establishing ‘‘AI for Sci￾ence’’ as the fifth scientific paradigm after experimentation,
VOLUME 13, 2025

 2025 The Authors. This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 License.
For more information, see https://creativecommons.org/licenses/by-nc-nd/4.0/ 215003

--- page 2 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
theory, computation, and data science. Beyond serving as
a mere tool for isolated tasks, AI is instigating a paradigm
shift across the entire scientific ecosystem. This evolution
of disciplines, driven by social and technological needs,
is characterized by the iterative restructuring of knowl￾edge systems—a hallmark of interdisciplinary convergence.
Within this context, rehabilitation science, a burgeoning
field central to human health, presents a prime frontier for
AI application. Although AI tools have been deployed for
specific challenges like intelligent sensing and rehabilitation
robotics, a substantial gap persists: the lack of a systematic,
AI-driven paradigm and knowledge engineering framework
for the entire rehabilitation science landscape.
In recent years, there have been few comprehensive
panoramic investigations and in-depth mining studies on
AI-driven rehabilitation science. Yang et al. [1] conducted
a preliminary bibliometric analysis on the application of AI
in rehabilitation science using CiteSpace software, but they
did not conduct further in-depth mining of disciplinary data,
nor did they adopt artificial intelligence strategies such as
machine learning and large models in their methodology.
Lanotte et al. [2] analyzed the clinical application of AI,
but their work lacked exploration of rehabilitation research
and knowledge engineering. Philipp et al. [3] reviewed
the application of classical machine learning, but failed to
perform systematic literature data mining. Mennella et al. [4]
presented a bibliometric review on rehabilitation tele-services
and intelligent assistance, without employing large models
for in-depth literature data mining. Chen et al. [5] compared
the natural language processing capabilities of large language
models (LLMs) in biomedicine, but did not involve knowl￾edge graph construction in rehabilitation science. Zhang et al.
[6] constructed biomedical knowledge graphs, but lacked AI
strategies tailored to emerging medical subfields such as reha￾bilitation. Wu et al. [7] demonstrated the application potential
of knowledge graphs in healthcare, while the application in
the field of rehabilitation science is still in its infancy.
Rehabilitation science is a typical emerging interdis￾ciplinary discipline integrating medicine and engineering.
It provides a large number of practical application scenarios
for general or basic disciplines. In addition to the aforemen￾tioned limited studies on comprehensive AI investigations
in rehabilitation and medical fields, research related to ‘‘AI
for Science’’ in basic or general disciplines offers essential
references and important insights for conducting relevant
research in rehabilitation science. However, due to the
more focused nature of the research object and field on
rehabilitation, as well as the rapid iteration and innovation
of AI itself, it is necessary to further analyze and adjust the
strategies of AI research paradigms based on the development
of the rehabilitation field and AI technology.
In terms of basic science and general technology:
Wang et al. [8] focused on the role of AI in accelerating
scientific discovery in basic disciplines, but did not involve
the investigation of emerging disciplines such as rehabilita￾tion. Musslick et al. [9] analyzed the practice of research
automation, but did not explore automated knowledge mining
in emerging rehabilitation disciplines. Angelopoulos et al.
[10] studied robotic automated discovery, but lacked the
machine cognitive computing link from literature analysis to
knowledge graph construction. Philipp et al. [3] constructed
parallel intelligence through interdisciplinary research on
complex systems, and the further implementation of data- and
knowledge-driven approaches could be explored.
AI serves as the core technological engine of the entire
‘‘AI for Science’’ initiative, and its technological iteration
provides solid support for empowering rehabilitation science
research.
In the field of natural language processing: The BERT
model proposed by Devlin et al. [11] demonstrates excellent
performance in text comprehension, but its application in
scientific literature analysis is still in the preliminary stage.
Peters et al. [12] advanced the development of natural
language processing (NLP), yet their method struggles to cap￾ture domain-specific semantics when processing professional
literature. Liu et al. [13] identified the insufficiency of LLMs
in literature and terminology processing.
In the field of data mining: Dinh et al. [14] systematically
elaborated that clustering is a key technology in data science,
and the application of clustering in disciplinary knowledge
discovery could be further explored. Aggarwal et al. [15]
made contributions to high-dimensional data dimensionality
reduction and clustering, but the adaptability of their methods
in processing text data remains to be verified. Liu et al.
[16] applied Variational Autoencoders for unsupervised
dimensionality reduction of text, and the dimensionality
reduction effects of different algorithms on disciplinary
text could be further analyzed and compared. Liu et al.
[17] proposed tensor representation for text, which could
be further improved and verified according to the needs
of disciplinary text mining. Heuer [18] conducted research
on text semantic comparison using t-SNE dimensionality
reduction for word vectors, and its application in semantic
research of disciplinary text could be further explored.
Situ [19] conducted comparative studies on manifold learn￾ing for dimensionality reduction, which could be further
improved by combining it with disciplinary text mining
problems. Lin and Zhou [20] used Latent Dirichlet Allocation
(LDA) to identify emerging technologies, and its knowledge
discovery capability could be enhanced by combining it with
NLP technologies such as LLMs. Benjamin Ampel et al.
[21] constructed a text analysis information system using
LLMs, which could be improved according to the needs of
interdisciplinary research. Davazdahemami et al. [22] built
an academic compass using LLM APIs, and its knowledge
mining capability in professional fields needs to be optimized
and enhanced.
In the field of knowledge graphs and related research:
Soman et al. [23] proposed the KG-RAG framework to
enhance the domain adaptability of general LLMs, but this
framework relies on the construction of knowledge graphs.
Dreger et al. [24] explored the extraction of knowledge graphs
215004 VOLUME 13, 2025

--- page 3 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
from materials science data using only LLMs, and its effec￾tiveness remains to be verified and improved. Dagdelen et al.
[25] evaluated the ability of LLMs to extract structured infor￾mation from materials chemistry texts, but did not involve
information extraction from disciplinary literature. Pan et al.
[26] explored collaborative reasoning between LLMs and
knowledge graphs, but lacked application verification in
disciplinary literature information extraction. Mo et al. [27]
improved the ability of LLMs to construct knowledge graphs
through clustering, and other strategies for enhancing LLM
information extraction could be studied. Pan et al. [28]
compared the opportunities and challenges of knowledge
computing between LLMs and knowledge graphs, and the
collaborative knowledge discovery between the two remains
to be explored. Desai et al. [29] studied knowledge graph
construction under different prompt strategies of LLMs, and
the impact of prompt engineering collaborating with mathe￾matical models could be explored. Kau et al. [30] analyzed
the computational efficiency of LLM and knowledge graph
integration strategies, and multi-model collaboration could
be considered to reduce overhead. Chaoguang et al. [31]
used multi-models to predict interdisciplinary topic links,
and heuristic knowledge graphs could be further constructed.
Zong et al. [32] summarized and prospected biomedical text
mining, and specific technical research could be carried out.
Nickel et al. [33] proposed knowledge representation learning
methods, and most existing knowledge graph research
focuses on general fields, with relatively few studies in
specific fields such as rehabilitation science. Boyko et al. [34]
summarized the interdisciplinary limitations of LLMs, laying
a foundation for adaptive technology research. Jeyaramet
al. [35] reconstructed text networks using LLMs, and their
method needs further improvement.
In summary, despite advancements in core AI, major
shortcomings persist in its integration with rehabilitation
science. These include: inadequate technical adaptability,
where general AI tools lack customization for the domain;
insufficient research depth, with a focus on single techniques
over multi-model collaboration; limited knowledge discov￾ery, staying at surface-level analysis rather than excavating
deep architectural patterns; incomplete domain coverage,
neglecting rehabilitation in favor of more established fields;
and lagging technological iteration, where knowledge graphs
lack updates from cutting-edge AI like LLMs.
To address these gaps, we move beyond traditional reviews
and bibliometrics to propose the RehabKD framework. This
innovative system is designed for multi-model collaborative
text mining and knowledge discovery, as shown in Figure 1.
The LLM-KG-LDACX engine leverages emerging AI to
extract information from a comprehensive dataset at the
intersection of AI and rehabilitation science.
Using the RehabKD framework, our study employs a
multifaceted approach—integrating the LLM-KG-LDACX
engine with sentiment analysis, manifold and cluster analysis,
complex networks, and topic discovery. This comprehensive
mining reveals the principal research trends, collaborative
TABLE 1. Data retrieval.
patterns, and underlying knowledge structures that character￾ize ‘‘AI for Science’’ in rehabilitation. Our work uncovers
latent patterns, traces evolutionary trends, and elucidates
intrinsic relationships among key elements. This study
provides valuable insights for researchers and clinicians
in rehabilitation and other emerging fields, promoting the
deeper integration and innovation of AI-driven scientific
discovery.
II. MATERIALS AND METHODS
A. DATA PREPROCESSING AND SEMANTIC VECTOR
MODEL
A key accumulation and outcome of interdisciplinary
research in emerging disciplines is the formation and
evolution of core knowledge repositories in the field. Web of
Science (WOS) is an internationally recognized high-quality
literature knowledge database. In this study, rehabilitation
science (as a representative of emerging disciplines) was
taken as the research subject, and the Web of Science Core
Collection database was used as the source of raw data.
The information in Table 1 was adopted as the retrieval
criteria. The retrieval strategy combined subject terms with
research fields, and the specific search formula was: (TS =
‘‘Rehabilitation’’ AND ‘‘Artificial Intelligence’’). A total of
719 articles were retrieved from the database up to December
25, 2024. From these, articles of the following document
types were excluded: ‘‘Retracted Publication’’, ‘‘Meeting
Abstract’’, ‘‘Letter’’, ‘‘Book Chapters’’, ‘‘Retraction’’, ‘‘Edi￾torial Material’’, and ‘‘Proceeding Paper’’. The remaining
699 articles after exclusion were used as the target dataset
for subsequent work. This time range covers the important
stages from the initial application of AI technology in
the rehabilitation field to the present. The literature data,
which are in English, were exported and stored in an Excel
file.
We first carried out necessary cleaning and preprocessing
of the text data. We carefully screened and removed duplicate
records and retracted records, and corrected data format
errors one by one. In the preprocessing stage of English
text data, toolkits such as NLTK (Natural Language Toolkit)
and WORDNET were used for natural language processing.
This mainly included: automatic word segmentation, removal
of punctuation marks, unification of lowercase letters,
stemming, part-of-speech tagging, term extraction, affix
processing, named entity recognition, removal of irrelevant
words such as articles, prepositions, conjunctions, etc., and
removal of stop words and other words without actual
semantic meaning, so as to convert unstructured text data into
structured data suitable for machine learning processing.
VOLUME 13, 2025 215005

--- page 4 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 1. RehabKD: Framework of knowledge discovery and data mining in rehabilitation.
The vectorization (word embedding) of text data is a
process of converting text into numerical vectors. By map￾ping to a vector space, it captures the semantic relationships
of words and supports natural language processing tasks.
Its essence lies in encoding semantic information so that
similar texts have similar representations in the vector space.
The mechanism is based on distributed semantics (where
the meaning of a word is determined by its context) and
neural network training (by optimizing the objective function
to make the word vectors of similar contexts closer in
distance). This provides a computable foundation for tasks
such as text classification and machine translation, as shown
in Algorithm 1 below. To balance semantic information
preservation and computational efficiency, we opted for 300-
dimensional semantic vectors as the embedded representation
of the research texts.
B. SEMANTIC SENTIMENT COMPONENT ANALYSIS
This study introduces a novel sentiment analysis framework
specifically designed for AI in rehabilitation literature. Our
method implements a hierarchical computational architecture
that progresses from words to sentences to entire paragraphs.
This structure quantifies two key dimensions: emotional
polarity (ranging from −1 for negative to 1 for positive)
and subjectivity (from 0 for objective to 1 for subjective).
The system first filters non-emotional elements by removing
technical terminology and common stopwords. Word-level
polarity computation combines VADER lexicon analysis with
domain-specific calibration and negation processing. For
subjectivity measurement, we enhance TextBlob’s baseline
Algorithm 1 Word Embedding Algorithm
scores through part-of-speech modifications, increasing
values for emotional adjectives while decreasing them
for neutral terms. The framework then aggregates these
results using specialized weighting schemes—part-of-speech
based weights for sentence-level computation and sentence￾length based weights for paragraph-level integration. This
215006 VOLUME 13, 2025

--- page 5 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
Algorithm 2 Sentiment Analysis Algorithm
approach provides precise emotional quantification to sup￾port decision-making processes in interdisciplinary research.
C. SEMANTIC SPACE DIMENSIONALITY REDUCTION AND
CLUSTERING
Clustering research on interdisciplinary datasets explores
semantic aggregation. 300 - dimensional text embeddings
preserve semantic information but demand high computa￾tional costs, thus requiring dimensionality reduction prior
to knowledge discovery. As shown in Algorithm 3 below,
we sampled different dimensionality reduction methods such
as Principal Component Analysis (PCA), Manifold Learning
(UMAP, t-SNE), Deep Learning (Autoencoders, Variational
Autoencoders), and Kernel Principal Component Analysis
(Kernel PCA). These methods generate low-dimensional
vectors with distinct features. We aim to explore whether
integrating these features through constructing tensors can
enhance the effectiveness of clustering analysis. We apply
K - Means, HDBSCAN, and Hierarchical clustering to low -
dimensional vectors from different algorithms, pure dimen￾sionality reduction tensors, and hybrid tensors combining
low - and high - dimensional vectors. For optimal results,
we integrate dimensionality reduction and clustering in
unsupervised learning, treating it as a multi - objective, multi -
parameter optimization problem and using Bayesian search
Algorithm 3 Dimensionality Reduction and Clustering
Algorithms
guided by evaluation metrics (silhouette coefficient, Davies -
Bouldin Index, Dunn Index) to optimize parameters such as
vector dimension, number of clusters, and hierarchical tree
height.
D. LATENT DIRICHLET ALLOCATION (LDA) MODEL
The LDA is a topic model based on Bayesian theory,
which is used to mine the la-tent topic structure of texts.
It assumes that a document is a mixture of multiple topics,
and topics are presented through the distribution of specific
words, with the words in a document being generated by
these topics. As shown in Algorithm 4 below, we first pre￾processed the literature texts (titles, abstracts, and keywords)
into word frequency vectors. The LDA model then carried
out iterative training based on these vectors. During the
training process, the probability distributions of topic words
and the prob-ability distributions of document topics were
updated. For example, parameters were adjusted to make
the words in the documents better fit their respective
topics.
VOLUME 13, 2025 215007

--- page 6 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
Algorithm 4 LDA Topic Model and Evolution Network
Analysis
E. COMPLEX NETWORK CONSTRUCTION
(CO-OCCURRENCE ANALYSIS METHOD)
Constructing a relationship network between keywords
through co - occurrence analysis and then using com￾plex network analysis methods to deeply explore various
structures and features of the network helps researchers
better understand the knowledge structure and potential
thematic relationships in the academic field. It pro-vides
strong support for further knowledge discovery, topic mining,
and information retrieval. As shown in Algorithm 5 below,
Algorithm 5 Co-occurrence Analysis Algorithm
co - occurrence analysis is a text mining method that reveals
the internal relationships between elements by counting their
co - occurrence patterns. It assumes that co - occurrence is
non - random (for example, the co - occurrence of academic
keywords reflects research topics). Its mechanism is as
follows: For the author - provided keywords in academic
papers, the co - occurrence frequency of keywords in the same
literature is counted to mine thematic associations. This helps
researchers discover the knowledge structure and trends in the
field and supports knowledge discovery and topic analysis.
F. COMPLEX NETWORK ANALYSIS (COMMUNITY
DETECTION)
Complex network analysis abstracts complex systems or
data relationships using graph structures. By combining
graph theory and network science methods, it analyzes node
attributes (such as degree, clustering coefficient, centrality,
etc.) and community structures, revealing the associations
between keywords and the overall characteristics of the
network. As shown in Algorithm 6 below, we mapped
215008 VOLUME 13, 2025

--- page 7 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
Algorithm 6 Complex Network Analysis Algorithm
elements to nodes and relationships to edges. By utilizing the
network topological structure and dynamic characteristics,
we studied the system functions. Through quantitative
analysis and visualization, we mined the internal laws
to achieve a structured analysis of complex relationships.
We employed the Louvain algorithm [36] to partition the
network into densely connected communities.
G. LLM-KG-LDACX MODEL AND KNOWLEDGE GRAPH
ENHANCEMENT
Information extraction of text entities and relationships is the
core of knowledge discovery research, which has undergone
several stages of development: dictionary-based methods,
rule-based methods, traditional machine learning methods,
deep learning methods, and pre-trained model methods.
In recent years, with the rise of large model technology,
knowledge discovery methods based on large models have
gradually become the latest frontier in the field of information
extraction and knowledge discovery.
The training of these information extraction models mainly
follows two paradigms or pathways: one is the NLU (Natural
Language Understanding) paradigm based on supervised
learning with annotated data, and the other is the NLG
(Natural Language Generation) paradigm based on unsu￾pervised generative learning with unannotated data (zero￾shot or few-shot). High-quality annotated datasets of SCI
literature form the foundation of the NLU supervised learning
paradigm. This arduous and time-consuming task requires
experienced senior professionals to devote significant effort
and resources to complete, which is extremely challenging
for rapidly developing emerging interdisciplinary fields such
as rehabilitation science.
In this study, we adopted the unsupervised generative
NLG information extraction paradigm. Without annotated
datasets, we first used API + Prompt to call a public
large language model (Alibaba’s Quark Qwen-Max) for
information extraction from the title text data in the target
discipline, obtaining the ‘‘LLM-KG.JSON’’ data. Here, the
Prompt standardized the behavior of the large model and
strictly restricted and constrained its output. On this basis,
we applied enhancement techniques to further calibrate
and supplement the extracted information, resulting in
‘‘LLM-KG-LDACX.JSON’’. The enhancement techniques
mainly include entity disambiguation using LDA (Latent
Dirichlet Allocation) and relationship enhancement using
co-occurrence matrices in complex networks, as shown in
Algorithm 7.
Subsequently, the previously established mathematical
models with independent data analysis and information
extraction capabilities—namely the Latent Dirichlet Allo￾cation (LDA) topic model and the co-occurrence matrix
of complex networks—were separately used to calibrate
and enhance the performance of the aforementioned large
language model, as shown in Algorithm 8 below. This pro￾cess thereby achieves multi-model collaborative information
extraction and knowledge graph construction.
III. RESULTS
A. ANALYSIS RESULTS OF THE DISCIPLINARY
DEVELOPMENT TREND
We first conducted a bibliometric analysis, geographical
analysis, and sentiment analysis of the literature information
of emerging disciplines. As shown in Figure 2, Figure 3,
and Figure 4 below, we comprehensively perceived the
cross-disciplinary situation of artificial intelligence in emerg￾ing disciplines through the number of published papers, the
spatial distribution of research findings, and the emotional
attitudes expressed in the texts by scientists.
The Figure 2 below shows the inclusion status of the Web
of Science (WOS) literature in the interdisciplinary field of
artificial intelligence within rehabilitation science. Literature
records began to appear in 2018. As of February 2025, the
VOLUME 13, 2025 215009

--- page 8 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
Algorithm 7 Information Extraction Algorithms of Large
Models
FIGURE 2. The trend of literature inclusion.
total number of published papers is 596, with an average
annual publication volume of 74.5 papers. The year with
the largest number of publications is 2024, with 201 papers
published.
The interdisciplinary research on artificial intelligence in
rehabilitation science has experienced a process from a slow
start to rapid development over the past two decades. The
upward trend in the number of published papers clearly
reflects the vigorous development of research in this field and
its increasingly important status.
The Figure 3 above shows the spatial distribution of
research institutions for the interdisciplinary research lit￾erature on rehabilitation science and artificial intelligence
included in WOS. Among them, the National University
of Singapore (with 36 papers), Shanghai Jiao Tong Uni￾versity (with 28 papers), and the University of Toronto
(with 26 papers) rank among the top three in terms of
the number of published papers. These institutions have
achieved more results in driving the development of emerging
disciplines with artificial intelligence. This may be related
to their respective technical re-serves in the field of artificial
intelligence and their strategic awareness of fully lever-aging
artificial intelligence to promote the rapid development
of emerging disciplines. The core element of emerging
discipline development is the community of scientists, and the
attitudes and emotions of scientists are crucial human factors
in scientific discovery.
The sentiment analysis results shown in Figure 4 below
hold significant reference value for accurately grasping
the current status, trends, and development drivers of
interdisciplinary research between rehabilitation science and
artificial intelligence (AI), and also provide useful insights
and guidance for subsequent research.
For literature title subjectivity, the average sentiment
subjectivity is 0.024 (low), indicating objective-oriented
abstracts; all scores concentrate in [0.0, 0.2], showing
research focuses on facts/data with minimal subjectivity.
For sentiment polarity, the average is 0.007 (slightly >
0), reflecting weak positive overall sentiment in the field:
positive (0.007, 5 articles, low proportion), negative (0.001,
1 article, rare), and neutral (0.991, 693 articles, dom￾inant), with most abstracts being objective/neutral and
focused on accurate research description. Overall, 99.140%
215010 VOLUME 13, 2025

--- page 9 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
Algorithm 8 LLM-KG-LDACX (Knowledge Graph Enhancement)
of scores concentrate in [-0.1, 0.1], confirming neutral,
highly concentrated sentiment with negligible extreme
ranges (non-dominant). Comprehensive analysis shows
small standard deviations: subjectivity (0.022, consistent
objectivity/standardization) and polarity (0.024, minimal
differences, high consistency/stability, strong emotional
expression consensus). In summary, this analysis shows
rehabilitation researchers hold highly consistent objectivity
and rationality towards AI-rehabilitation interdisciplinary
research.
Below, we will demonstrate the sentiment analysis
algorithm in the RehabKD framework using the following
text.
Demonstration Text: AI has been transformative in reha￾bilitation, with impressively effective personalized protocols
and exciting movement-decoding breakthroughs. Yet frus￾trating limitations persist: disturbing biases, prohibitive costs,
and risks of eroding clinician-patient rapport. Encouragingly,
solutions emerge, keeping its trajectory overwhelmingly
promising.
VOLUME 13, 2025 215011

--- page 10 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 3. Distribution of major research institutions worldwide.
FIGURE 4. Histogram of sentiment subjectivity scores and sentiment polarity distribution.
As shown in Figure 5 below, the algorithm’s entire
process—including the top-down hierarchical division of
text into ‘‘paragraphs → sentences → components →
phrases/words’’ and the subsequent bottom-up detection
and calculation of sentiment components in the text—is
demonstrated in the form of a recursive tree.
B. RESULTS OF KEYWORD ANALYSIS
The WOS literature on artificial intelligence’s participation
in rehabilitation science research first emerged in 2018. With
the gradual deepening of interdisciplinary research, Figure 6
below presents the annual changing trends of the word cloud
distribution.
We further conducted a word frequency analysis of the
keyword terms in recent years. As shown in TABLE 2
below, the following main changing trends are presented. The
popularity of core technology-related vocabulary continues
to rise: The word frequencies of ‘‘artificial intelligence’’
and ‘‘machine learning’’ have ranked among the top in
all time periods, and they show an overall upward trend.
There has been a significant increase from 2018-2019 to
2022-2023, indicating that these two technologies have
always been in a core position in the research and the
degree of attention to them is constantly increasing. The
popularity of rehabilitation-related vocabulary is relatively
stable: Although the word frequency of the word ‘‘rehabilita￾tion’’ fluctuates, it has al-ways maintained a certain quantity,
indicating that the field of rehabilitation is a continuous
research direction. At the same time, scenarios combined
with rehabilitation, such as ‘‘patient rehabilitation’’ and
‘‘neural rehabilitation’’, also appear, reflecting the continuous
existence of applied research of technologies in the field of
rehabilitation.
Emerging technology-related vocabulary appears alter￾nately: Different emerging technology-related vocabulary
enters the list of high-frequency words in different periods.
In the early stage, words like ‘‘Internet of things’’ were among
them, and in the later stage, words such as ‘‘augmented
reality’’ and ‘‘virtual reality’’ emerged. This indicates that
the research hotspots are constantly changing with the
215012 VOLUME 13, 2025

--- page 11 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 5. Demonstration of sentiment calculation for a single text and its recursive tree.
FIGURE 6. Word cloud of keywords.
development of technology, and new technological concepts
keep emerging and attracting attention.
Close connection with the medical and health field: In
addition to rehabilitation, words such as ‘‘healthcare’’, ‘‘dis￾ease’’ (e.g., ‘‘Parkinson’s disease’’, ‘‘diabetes’’) frequently
appear. This shows that the research is closely related to
the medical and health field, and using technology to solve
medical and health problems is an important part of the
research content.
C. RESULTS OF SEMANTIC SPACE CLUSTERING
EXPLORATION
We employed three clustering algorithms—K-Means, HDB￾SCAN, and hierarchical clustering—to conduct clustering
analysis on the title data in the target dataset. Prior to
clustering, we processed the data using eight dimensionality
reduction methods: no dimensionality reduction, Principal
Component Analysis (PCA), Uniform Manifold Approxima￾tion and Projection (UMAP), t-distributed Stochastic Neigh￾bor Embedding (t-SNE), Autoencoder (AE), Variational
Autoencoder (VAE), Kernel Principal Component Analysis
(KernelPCA), and integrated tensor. Each strategy underwent
100 iterations of optimization. We used violin plots to
comprehensively examine the aforementioned clustering
analyses and dimensionality reduction processes, as shown
in Figure 7 below. The three violin plots correspond to
the three clustering algorithms respectively; each violin plot
contains three violins, which correspond to three evaluation
metrics; within each violin, there are eight points of different
colors, representing the eight data dimensionality reduction
strategies. We evaluated the quality of clustering results from
different perspectives using various metrics: a higher Silhou￾ette Coefficient score (closer to 1) indicates better cluster
separation; a higher Calinski-Harabasz Index means clearer
cluster definition; and a lower Davies-Bouldin Index (closer
to 0) signifies better cluster compactness. Additionally, wider
violin plots indicate more stable performance during the
iteration process.
The violin plots in Figure 7 above actually comprehen￾sively reflect the results of the three types of clustering
VOLUME 13, 2025 215013

--- page 12 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
TABLE 2. Term frequency.
FIGURE 7. Clustering violin plots.
performed after dimensionality reduction processing using
different strategies, as presented in Figures 8, 9, and 10
below. In the following, we will conduct an in-depth and
detailed examination of the specific conditions of each type
of clustering.
We selected eight strategies to optimize the title data
in the target dataset. We plotted optimization curves for
100 iterations, traced back the optimal clustering from each
strategy, and presented the 2D visualization graph of this
optimal clustering above the training curve. To facilitate the
comparison of clustering results across different strategies,
we plotted histograms, further generated corresponding radar
charts from the histograms, and comprehensively calculated
and evaluated the clustering performance of different strate￾gies using the following indicator formula (see Formula 1),
its parameters s, c, and d represent ‘‘Silhouette’’, ‘‘Calinski’’,
and ‘‘Davies’’ indicator respectively.
ComprehensiveScore := 0.4 ∗ s + 0.35 ∗ c + 0.25 ∗ d (1)
We present the computational analysis results of K-Means in
detail from bottom to top in Figure 8 above, and in the eval￾uation of K-Means clustering performance across different
dimensionality reduction strategies: KernelPCA ranks first
with a comprehensive score of 0.951 (Silhouette coefficient:
0.896, Calinski-Harabasz Index: 99935.348, Davies-Bouldin
Index: 0.29), followed by AE in second place with a
comprehensive score of 0.904 (Silhouette coefficient: 0.788,
Calinski-Harabasz Index: 96396.893, Davies-Bouldin Index:
0.424), UMAP in third with 0.802 (Silhouette coefficient:
0.638, Calinski-Harabasz Index: 24151.5, Davies-Bouldin
Index: 0.415), t-SNE in fourth with 0.778 (Silhouette
coefficient: 0.608, Calinski-Harabasz Index: 17911.918,
215014 VOLUME 13, 2025

--- page 13 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
Davies-Bouldin Index: 0.499), Tensor Construction in fifth
with 0.731 (Silhouette coefficient: 0.561, Calinski-Harabasz
Index: 7107.451, Davies-Bouldin Index: 0.509), PCA in sixth
with 0.729 (Silhouette coefficient: 0.554, Calinski-Harabasz
Index: 7332.833, Davies-Bouldin Index: 0.524), No Reduc￾tion in seventh with 0.710 (Silhouette coefficient: 0.55,
Calinski-Harabasz Index: 4176.849, Davies-Bouldin Index:
0.547), and VAE in eighth with 0.660 (Silhouette coefficient:
0.525, Calinski-Harabasz Index: 1222.436, Davies-Bouldin
Index: 0.656); as can be observed from the radar chart
and histogram, top-ranked dimensionality reduction methods
such as KernelPCA perform better across various evaluation
metrics, and the clustering graphs and training curves further
demonstrate the differences in K-Means clustering perfor￾mance under different dimensionality reduction methods—
for instance, the clustering distribution and indicator variation
trends of methods like AE and KernelPCA are consistent with
the aforementioned score rankings.
We present the computational analysis results of HDB￾SCAN in detail from bottom to top in Figure 9 above,
and in the evaluation of HDBSCAN clustering performance
across different dimensionality reduction methods: AE ranks
first with a comprehensive score of 0.745 (Silhouette coef￾ficient: 0.725, Calinski-Harabasz Index: 1321.264, Davies￾Bouldin Index: 0.557), followed by UMAP in second place
with a comprehensive score of 0.667 (Silhouette coeffi￾cient: 0.551, Calinski-Harabasz Index: 1119.001, Davies￾Bouldin Index: 0.663), No Reduction in third with 0.588
(Silhouette coefficient: 0.567, Calinski-Harabasz Index:
205.034, Davies-Bouldin Index: 2.052), t-SNE in fourth
with 0.586 (Silhouette coefficient: 0.402, Calinski-Harabasz
Index: 1003.47, Davies-Bouldin Index: 1.394), PCA in fifth
with 0.576 (Silhouette coefficient: 0.557, Calinski-Harabasz
Index: 154.195, Davies-Bouldin Index: 1.993), VAE in sixth
with 0.533 (Silhouette coefficient: 0.483, Calinski-Harabasz
Index: 88.736, Davies-Bouldin Index: 1.859), KernelPCA in
seventh with 0.517 (Silhouette coefficient: 0.46, Calinski￾Harabasz Index: 54.078, Davies-Bouldin Index: 1.576),
and Tensor Construction in eighth with 0.497 (Silhou￾ette coefficient: 0.263, Calinski-Harabasz Index: 230.022,
Davies-Bouldin Index: 0.946); as can be observed from
the radar chart and histogram, top-ranked dimensionality
reduction methods such as AE perform better across various
evaluation metrics, and the clustering graphs and training
curves further demonstrate the differences in HDBSCAN
clustering performance under different dimensionality reduc￾tion methods—for instance, the clustering distribution and
indicator variation trends of methods like AE and UMAP are
consistent with the aforementioned score rankings.
We present the computational analysis results of hierar￾chical clustering in detail from bottom to top in Figure 10
above and Figure 11 below. In the evaluation of hierarchi￾cal clustering performance across different dimensionality
reduction methods: AE ranks first with a comprehen￾sive score of 0.915, achieving a Silhouette coefficient of
0.781, a Calinski-Harabasz Index of 156482.913, and a
Davies-Bouldin Index of 0.429; followed by KernelPCA in
second place with a comprehensive score of 0.863 (Silhouette
coefficient: 0.568, Calinski-Harabasz Index: 399313.024,
Davies-Bouldin Index: 0.27); UMAP in third with 0.841
(Silhouette coefficient: 0.625, Calinski-Harabasz Index:
95250.571, Davies-Bouldin Index: 0.285); t-SNE in fourth
with 0.822 (Silhouette coefficient: 0.484, Calinski-Harabasz
Index: 257906.175, Davies-Bouldin Index: 0.038); PCA in
fifth with 0.781 (Silhouette coefficient: 0.434, Calinski￾Harabasz Index: 136013.857, Davies-Bouldin Index: 0.071);
Tensor Construction in sixth with 0.686 (Silhouette coeffi￾cient: 0.366, Calinski-Harabasz Index: 14236.435, Davies￾Bouldin Index: 0.039); No Reduction in seventh with
0.642 (Silhouette coefficient: 0.34, Calinski-Harabasz Index:
4606.419, Davies-Bouldin Index: 0.017); and VAE in eighth
with 0.623 (Silhouette coefficient: 0.458, Calinski-Harabasz
Index: 911.485, Davies-Bouldin Index: 0.68). As can be
observed from the radar chart and histogram, top-ranked
dimensionality reduction methods such as AE perform better
across various evaluation metrics, while the clustering graphs
and training curves further demonstrate the differences in
hierarchical clustering performance under different dimen￾sionality reduction methods—for instance, the clustering
distribution and indicator variation trends of methods like AE
and KernelPCA are consistent with the aforementioned score
rankings. The results of the above hierarchical clustering
are further presented using a dendrogram, as shown in
Figure 11 below. Among different strategies, AE performs
best in hierarchical clustering and is presented separately in
an enlarged view.
From the ablation experiments and the ranking of various
performance indicators of the three aforementioned cluster￾ing algorithms, it can be seen that Kernel PCA achieves
the best comprehensive performance in K-Means, AE shows
the optimal effect in HDBSCAN, and AE also performs
prominently in hierarchical clustering. Through stability
evaluations such as analysis of variance (ANOVA), K-Means
exhibits more stable overall performance, HDBSCAN has
relatively large variability, and the stability of hierarchical
clustering is at an intermediate level. Meanwhile, although
the tensor fusion strategy has been optimized, its effect
does not surpass that of single dimensionality reduction
methods—this may be due to the large differences in feature
spaces among different dimensionality reduction methods,
where simple concatenation leads to information redundancy.
Additionally, various visualization charts (dendrograms,
radar charts, histograms, violin plots, etc.) clearly present the
clustering effects and performance differences of different
algorithms combined with dimensionality reduction methods,
comprehensively demonstrating the clustering performance
of each algorithm under optimal configurations.
D. TEMPORAL SEQUENCE OF LDA TOPIC MINING AND
ITS EVOLUTION NETWORK
According to Web of Science retrieval results, the earliest
interdisciplinary research on artificial intelligence (AI) in the
VOLUME 13, 2025 215015

--- page 14 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 8. K-means dimensionality reduction and clustering results.
215016 VOLUME 13, 2025

--- page 15 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 9. HDBSCAN dimensionality reduction and clustering results.
VOLUME 13, 2025 215017

--- page 16 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 10. Results of hierarchical clustering.
215018 VOLUME 13, 2025

--- page 17 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 11. Results of hierarchical clustering (dendrogram).
field of rehabilitation science emerged in 2018. To explore the
evolution process of AI-driven research topics in emerging
disciplines, we divided the literature on AI-interdisciplinary
research in rehabilitation science from 2018 to 2025 into time
slices. The LDA (Latent Dirichlet Allocation) model was then
used to conduct topic mining on the keywords of each time
segment. Based on the topics mined from the time slices of
each year, the corresponding temporal sequence array and
research topic evolution network were constructed, as shown
in Figure 12 below.
This network was built based on the cosine similarity
between TF-IDF vectorized topic representations. An edge
was established when the similarity exceeded the threshold
θ = 0.15, and the direction of the edge was marked
according to the temporal evolution direction. The finally
generated directed graph contained 40 nodes and 63 edges.
The importance of nodes was quantified using a comprehen￾sive evolution importance index, which integrated multiple
centrality measures. The calculation formula is shown in
Formula 2:
Ei = 0.4
w_outi
max(wout)
+ 0.2
deg_outi
max(degout)
+ 0.2
SOIi
max(SOI)
+ 0.1
PDi
max(PD)
+ 0.1
PRi
max(PR)
(2)
where w_outi represents the weighted out-degree, deg_outi
denotes the number of out-degrees, SOIi stands for secondary
influence, PDi refers to propagation depth, and PRi corre￾sponds to PageRank centrality. Analysis identified 2022-T4
(0.787), 2023-T1 (0.759), and 2022-T1 (0.67) as the most
influential nodes, which play a key role in topic propagation
and evolution paths within the network structure. The longest
VOLUME 13, 2025 215019

--- page 18 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 12. Topic evolution network of ai-interdisciplinary research in rehabilitation science.
TABLE 3. LDA theme discovery in 2018.
propagation path is (2019-T1, 2020-T4, 2021-T3, 2022-T2,
2023-T4, 2024-T4, 2025-T4).
In the evolution network array shown in Figure 12 above,
the annual topic time slices corresponding to each column
are presented in Tables 3 to 10 below. Meanwhile, Table 11
provides a comprehensive summary of the overall LDA topic
detection results over the 8-year period (2018–2025).
TABLE 3 above presents a summary of the focused issues
of each Topic and the application of AI technologies in 2018.
For example: Topic 1 addressed ‘‘parkinson’s dis-ease,’’
‘‘patient rehabilitation,’’ ‘‘stroke patients,’’ ‘‘late - stage
parkinson’s disease,’’ and ‘‘fugl-meyer stroke rehabilitation
protocol,’’ applying ‘‘machine learning - based evaluations’’
and integrating with ‘‘medical image processing,’’ ‘‘fugl
- meyer guidelines,’’ ‘‘spatiotemporal feature extraction,’’
‘‘marker - less multicamera setup,’’ and ‘‘patient motion’’.
TABLE 4 above presents a summary of the focused issues
of each topic and the application of AI technologies in
2019. Such as: Topic 1 addressed ‘‘stroke’’, ‘‘paralyzed’’,
and ‘‘healthcare’’, utilizing ‘‘inverse kinematics’’, ‘‘deep
learning system’’, ‘‘intelligent solutions’’, and ‘‘artificial
muscle intelligence’’, and integrating with ‘‘exoskeleton’’,
‘‘assistive technologies’’, and ‘‘eeg’’.
TABLE 5 above presents a summary of the focused
issues of each Topic and the application of AI technologies
in 2020. For instance: Topic 4 concentrated on ‘‘chronic
stage stroke’’, ‘‘qual-ity of life’’, ‘‘rehabilitation’’, and
‘‘cognitive rehabilitation’’, using ‘‘artificial intelligence’’ and
‘‘machine learning’’, and integrating with ‘‘virtual reality’’
and ‘‘exoskeleton’’.
TABLE 6 above presents a summary of the focused issues
of each Topic and the application of AI technologies in
2021. For examples: Topic 3 dealt with ‘‘stroke’’, ‘‘chronic
diseases’’, and ‘‘personalization’’, implementing ‘‘artificial
intelligence’’, ‘‘deep learning’’, and ‘‘machine learning’’,
and integrating with ‘‘brain - computer interface’’, ‘‘3d
215020 VOLUME 13, 2025

--- page 19 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
TABLE 4. LDA theme discovery in 2019.
TABLE 5. LDA theme discovery in 2020.
TABLE 6. LDA theme discovery in 2021.
printing’’, and ‘‘wearable technology’’. Topic 4 centered on
‘‘diagnosis’’, ‘‘rehabilitation’’, ‘‘pharma industry 4’’, and
‘‘medical cyber - physical systems’’, applying ‘‘machine
learning’’, ‘‘deep learning’’, ‘‘artificial intelligence’’, and
‘‘classification’’, and combining with ‘‘wearable computing
and electronics’’ and ‘‘robotics’’.
TABLE 7 above presents a summary of the focused
issues of each Topic and the application of AI technologies
in 2022. Such as: Topic 1 focused on ‘‘rehabilitation’’,
‘‘covid - 19’’, and ‘‘alzheimer’s disease’’, utilizing ‘‘artificial
intelligence’’, ‘‘machine learning’’, ‘‘deep learning’’, ‘‘con￾volutional neural network’’, and ‘‘pattern recognition’’, and
integrating with ‘‘sensors’’. Topic 4 concentrated on ‘‘reha￾bilitation’’, ‘‘neurorehabilitation’’, ‘‘multiple sclerosis’’, and
‘‘digital health’’, using ‘‘artificial intelligence’’, ‘‘machine
learning’’, and ‘‘deep learning’’, and combining with ‘‘virtual
reality’’.
TABLE 8 above presents a summary of the focused issues
of each Topic and the application of AI technologies in
2023. Such as: Topic 1 focused on ‘‘rehabilitation’’, ‘‘stroke’’,
‘‘covid - 19’’, and ‘‘prediction’’, utilizing ‘‘artificial intelli￾gence’’, ‘‘machine learning’’, ‘‘deep learning’’, ‘‘gpt - 4’’, and
‘‘chatgpt’’.
TABLE 9 above presents a summary of the focused
issues of each Topic and the application of AI technologies
in 2024. For example: Topic 2 centered on ‘‘stroke’’,
applied ‘‘artificial intelligence’’, ‘‘machine learning’’, and
‘‘deep learning’’, integrating with ‘‘emg’’, ‘‘brain - computer
interface’’, and ‘‘virtual reality’’.
TABLE 10 above presents a summary of the focused medi￾cal issues of each topic and the application of AI technologies
in 2025. Such as: Topics 4 dealt with ‘‘stroke’’ and ‘‘gait
rehabilitation’’, applying ‘‘artificial intelligence’’, ‘‘machine
learning for engineering applications’’, and ‘‘deep learning
VOLUME 13, 2025 215021

--- page 20 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
TABLE 7. LDA theme discovery in 2022.
TABLE 8. LDA theme discovery in 2023.
TABLE 9. LDA theme discovery in 2024.
TABLE 10. LDA theme discovery in 2025.
for engineering applications’’, integrating with ‘‘data-driven
simulation’’, ‘‘evolutionary computation’’, ‘‘model-based
systems engineering’’, ‘‘data-driven engineering’’, and ‘‘six￾bar linkage mechanism’’.
TABLE 11 above presents a summary of the focused
issues of each topic and the application of AI technologies
from 2018 to 2025. Topic 0 focused on ‘‘rehabilitation’’,
‘‘telemedicine’’, and ‘‘education’’, implementing ‘‘artificial
intelligence’’, ‘‘machine learning’’, ‘‘deep learning’’, ‘‘com￾putational intelligence’’, and ‘‘artificial neural networks’’,
and integrating with ‘‘brain-computer interface’’. Topic
1 centered around ‘‘rehabilitation’’ and ‘‘stroke’’, applying
‘‘artificial intelligence’’, ‘‘machine learning’’, and ‘‘deep
learning’’, and combining them with ‘‘virtual reality’’,
‘‘augmented reality’’, and ‘‘robotics’’. Topic 2 concentrated
on ‘‘rehabilitation’’, ‘‘stroke’’, and ‘‘bibliometric analysis’’,
utilizing ‘‘artificial intelligence’’ and ‘‘machine learning’’
in conjunction with ‘‘internet of things’’. Topic 3 was
215022 VOLUME 13, 2025

--- page 21 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
TABLE 11. LDA theme discovery from 2018 to 2025.
concerned with ‘‘rehabilitation’’, ‘‘diagnosis’’, ‘‘stroke’’,
‘‘rehabilitation medicine’’, and ‘‘e-health’’, applying ‘‘artifi￾cial intelligence’’, ‘‘deep learning’’, ‘‘machine learning’’, and
‘‘neural network’’, and integrating with ‘‘robotics’’. Topic
4 focused on ‘‘rehabilitation’’, ‘‘stroke’’, ‘‘healthcare’’, and
‘‘review’’, implementing ‘‘artificial intelligence’’, ‘‘ma-chine
learning’’, and ‘‘deep learning’’, and combining them with
‘‘virtual reality’’, ‘‘computer vision’’, and ‘‘robotics’’.
E. RESULTS OF COMPLEX NETWORK COMMUNITY
DETECTION
We constructed a complex network through the keyword￾term co-occurrence matrix and applied the Louvain algorithm
for community detection, deriving the key results shown in
Figure 13 and Table 12 below.
Regarding the topological indicators of the complex
network, the average degree is 13.656. This implies that,
on average, each node in the entire network has a connection
with roughly 14 other nodes. It reflects that there is a
certain level of common connection among the keywords,
yet they are not extremely closely linked, indicating that
the network possesses a certain degree of diversity and
complexity. The maximum degree amounts to 1331, which
reveals that there are very few ‘‘core’’ key-words with
extremely high connectivity in the network. These keywords
may serve as crucial hubs in the whole knowledge network,
exerting extensive associative influences on numerous other
keywords, and are highly likely to represent the core themes
or popular research directions within the research field.
The average clustering coefficient is 0.892. The relatively
high value close to 1 demonstrates that the network has
strong clustering properties. That is to say, keywords with
co-occurrence relationships tend to form compact small
groups. This indicates that in the research field, related
keywords usually cluster around specific themes or research
directions, forming relatively independent knowledge clus￾ters with close internal connections. The maximum clustering
coefficient is 1.0, which further validates the existence
of some completely closely connected small groups in
the network. These small groups may represent highly
specialized research subfields or specific research hotspots
with extremely high internal correlation.
Through the Louvain algorithm, 34 communities were
discovered, and the modularity is 0.533. Since the modularity
is greater than 0.3, it indicates that the division of communi￾ties has a high degree of rationality and effectiveness. The
in-ternal connections within each community are tight, while
the connections between communities are relatively sparse,
clearly demonstrating the modular structure of the research
field. TABLE 3 below lists the communities discovered in
Figure 13 above.
F. EXTERNAL VALIDATION OF LLM-KG-LDACX AND
KNOWLEDGE GRAPH CONSTRUCTION
PubMed was used as an external validation dataset to
further understand and verify the model’s capability and
reliability. The biLSTM-CRF model and BERT model were
selected as reference models for comparing knowledge
discovery methods. The biLSTM-CRF deep learning model
is a common baseline model in the field of information
extraction, while the BERT pre-trained model is a state￾of-the-art (SOTA) model with excellent performance in the
field of natural language processing (NLP) in recent years.
Both the biLSTM-CRF model and BERT model were trained
using the supervised learning paradigm (NLU), with training
conducted on SciER [37]—an open high-quality annotated
dataset for the scientific text domain. Four models (biLSTM￾CRF, BERT, LLM-KG, and LLM-KG-LDACX) were used
to perform information extraction on 699 high-quality SCI
text data entries in the intelligent rehabilitation field. PubMed
was then used for external validation and evaluation of the
extraction results, including: entity recognition verification
statistics, relationship co-occurrence support, relationship
exact match, and corresponding support rates, as shown in
Figure 14 below.
The authoritative PubMed dataset was used to conduct
external validation on multiple sets of quantitative indicators
for entity recognition and relationship extraction results of
the four models (biLSTM-CRF, BERT, LLM-KG, LLM-KG￾LDACX), as shown in Figure 14 above. The total number
of entities of the four models was 358, 827, 1667, and
1659, respectively; among these, the number of entities
supported by PubMed was 286, 786, 1137, and 1133,
with corresponding entity support rates of 79.89%, 95.04%,
68.21%, and 68.29%. The total number of relationships
was 381, 1944, 1336, and 4355, respectively; the number
of relationships with co-occurrence support was 281, 1823,
960, and 3247, with co-occurrence support rates of 73.75%,
93.78%, 71.86%, and 74.56% in sequence; the number of
relationships with exact match support was 141, 936, 276, and
531, with exact support rates of 37.01%, 48.15%, 20.66%,
VOLUME 13, 2025 215023

--- page 22 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 13. Community detection in the complex network of keyword co-occurrences.
FIGURE 14. PubMed external validation comparison of information extraction by biLSTM, BERT, LLM-KG, and LLM-KG-LDACX models.
and 12.19%, respectively. The LLM-KG-LDACX model
exhibited excellent performance in text entity recognition
and relationship extraction. In fact, many entities and
relationships identified by the LLM-KG-LDACX model
were correct but not supported by PubMed validation
(e.g., the triple ‘‘source: Support Vector Machine-Based
Classifier; relationship: Used For; target: Assessment of
Finger Movement’’). This may be due to a certain lag in
PubMed data annotation updates or limitations in specific
professional domains, which fully demonstrates the great
potential of the LLM-KG-LDACX model for knowledge
discovery in unannotated data.
Using PubMed literature data as the external validation
benchmark, the performance of the four information extrac￾tion models (biLSTM-CRF, BERT, LLM-KG, LLM-KG￾LDACX) was evaluated. Four core indicators—Accuracy,
Completeness, Connectivity, and Redundancy—were used to
quantify model performance, as shown in Figure 15 below.
The performance of the four models’ information extrac￾tion results (without redundancy processing) is shown in
215024 VOLUME 13, 2025

--- page 23 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
TABLE 12. Keyword communities detection.
the left panel of Figure 15 above: biLSTM-CRF had an
Accuracy of 1.0, Completeness of 0.0, Connectivity of 2.33,
and Redundancy of 0.02; BERT had an Accuracy of 1.0,
Completeness of 0.01, Connectivity of 5.52, and Redundancy
of 0.03; LLM-KG had an Accuracy of 1.0, Completeness
of 0.01, Connectivity of 1.74, and Redundancy of 0.0;
LLM-KG-LDACX had an Accuracy of 1.0, Completeness
of 0.01, Connectivity of 5.96, and Redundancy of 0.19.
After redundancy processing (data cleaning) of the four
models’ information extraction results, the quantitative
performance of the four core indicators is shown in the
right panel of Figure 15 above: the Redundancy of all
models decreased to 0.0, while other indicators showed slight
adjustments: biLSTM-CRF’s Connectivity decreased from
2.33 to 2.25, with Accuracy and Completeness remaining
1.0 and 0.0; BERT’s Connectivity decreased from 5.52 to
5.12, with Accuracy and Completeness remaining 1.0 and
0.01; LLM-KG showed minimal changes, with Accuracy of
1.0, Completeness of 0.01, Connectivity of 1.72, and only
Redundancy decreasing from 0.0 to 0.0; LLM-KG-LDACX
had a Connectivity of 4.83, with Accuracy and Complete￾ness remaining 1.0 and 0.01, respectively. The redundancy
processing achieved a significant effect (Redundancy of
all models decreased to 0.0) without significant loss of
VOLUME 13, 2025 215025

--- page 24 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 15. Knowledge graph evaluation indicators.
Completeness (average change of 0.0). The BERT pre-trained
model—trained via supervised learning on high-quality
annotated data—performed excellently as a SOTA model.
The unsupervised generative models (LLM-KG and LLM￾KG-LDACX) maintained comparable Completeness (0.01)
to BERT (0.01) and slightly higher than biLSTM-CRF
(0.0) after data cleaning. In particular, LLM-KG-LDACX
fully demonstrated great potential in zero-shot or few￾shot information extraction tasks with its relatively high
Connectivity.
The JSON file obtained from information extraction
by the LLM-KG-LDACX model was used to construct
the corresponding knowledge graph via visualization. The
important and representative parts of this graph are presented
below.
The above Figure 16 shows the largest subgraph of
the interdisciplinary knowledge graph. The central node is
‘‘artificial intelligence’’, which serves as the core hub of the
entire system. This subgraph can be divided into the core
technology layer, the application technology support layer,
and the industry application layer. The architecture comprises
three main layers. The Core Technology Layer features
‘‘Machine learning,’’ a pivotal element adjacent to the core
node, serving as the bedrock for artificial intelligence. It pro￾vides the algorithmic framework enabling AI models to learn,
induce, and predict, facilitating intelligent behavior. The
Application Technology Sup-port Layer encompasses diverse
nodes. Sensors and Detection Technologies, including ‘‘low￾cost pressure sensor matrix,’’ ‘‘wearable technology,’’ and
electromyography - related nodes, supply abundant raw
data for AI. Data Analysis and Interpretation nodes, such
as ‘‘human activity recognition’’ and ‘‘digital biomarkers,’’
showcase AI’s capacity to process and transform multi -
source data into actionable insights. Additionally, nodes
like ‘‘serious games,’’ ‘‘blockchain,’’ ‘‘virtual reality,’’ and
‘‘advanced materials’’ represent collaborative fields where
AI is applied across various domains. Finally, the Industry
Application Layer spans multiple sectors. In healthcare,
nodes including ‘‘diagnosis and management of chronic
conditions,’’ ‘‘stroke patients,’’ and ‘‘spinal cord in-jury reha￾bilitation’’ highlight AI’s role in disease diagnosis, treatment,
and health management. In the sports rehabilitation field,
nodes such as ‘‘anterior cruciate ligament injuries,’’ ‘‘action
recognition,’’ and ‘‘fatty degeneration’’ demonstrate its appli￾cation in sports injury prevention, diagnosis, rehabilitation,
and training optimization.
The above Figure 17 shows partial independent subgraphs
of the knowledge graph. Subgraph a, focuses on ‘‘ai’’,
illustrating its technical chain in stroke diagnosis, treatment,
and rehabilitation prediction. Subgraph b, ‘‘motion control’’,
highlights the key roles of artificial neural molecular systems
and robotic arms in rehabilitation motion control. Subgraph
c, ‘‘spine’’, reveals the application potential of neurotrophic
nodes and human-computer interaction technologies in spinal
medical rehabilitation. Subgraph d, centered on ‘‘soldier
musculoskeletal health’’, demonstrates the integrated use
of multiple technologies, including personalized digital
hormones, for managing soldiers’ musculoskeletal health.
Subgraph e, ‘‘wearable device’’, shows how ChatGPT￾4 enables intelligent exercise therapy for osteoarthritis
and sarcopenia using wearable devices. Subgraph f, based
on ‘‘psychosocial rehabilitation research’’, presents the
ap-plication patterns of large language models and text
mining in addressing psychosocial rehabilitation issues.
Subgraph g, ‘‘metaverse’’, explores intervention paradigms
and values for cognitive decline. Subgraph h, ‘‘robotic
rehabilitation system’’, depicts the technical architecture and
application process of postoperative robotic rehabilitation
systems. Subgraph i, focusing on ‘‘cognitive function’’,
showcases research on cognitive function after brain tumor
radiotherapy using the Oracle AI platform. Subgraph j
‘‘management of stroke disorders’’, respectively demonstrate
the applications of natural language processing and machine
learning in stroke and cross-disease management. Subgraph
k, centered on ‘‘older patients’’, shows how machine learning
combined with systems theory optimizes home rehabilitation
programs for elderly patients after hip replacement surgery.
Finally, subgraph l, ‘‘human digital twin’’, emphasizes
215026 VOLUME 13, 2025

--- page 25 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 16. The largest subgraph in the interdisciplinary knowledge graph.
its crucial role and technical support in personalized
medicine.
IV. DISCUSSION
A. DISCUSSION OF THE RESULTS
To address these gaps, we establish the RehabKD framework,
which integrates a suite of machine learning models, notably
the LLM-KG-LDACX engine. This framework enables a
comprehensive computational analysis of the literature on
AI-driven interdisciplinary research in rehabilitation science.
Our work reveals key insights into developmental trends, core
technologies, and knowledge structures within this emerging
field.
Interdisciplinary research between rehabilitation science
and AI has grown exponentially since 2018, peaking in 2024.
Leading institutions like the National University of Singapore
are prominent contributors, reflecting a strategic focus on
AI. Sentiment analysis of abstracts shows consistently low
subjectivity and a neutral sentiment proportion of 0.991,
indicating a highly objective and rational research discourse.
Term frequency analysis identifies ‘‘artificial intelligence’’
and ‘‘machine learning’’ as central and rising technolo￾gies. The evolving vocabulary highlights shifting research
priorities.
We applied multiple dimensionality reduction strategies,
including manifold learning and autoencoders, to cluster
high-dimensional semantic vectors. Our evaluation shows
that Kernel PCA with K-Means delivered the best overall per￾formance, while autoencoders, when paired with HDBSCAN
and hierarchical clustering, achieved the highest clustering
scores on specific metrics. Ablation experiments confirmed
that a comprehensive information tensor integrating multiple
strategies did not surpass clustering based on individual
methods. Keyword co-occurrence and complex network anal￾yses reveal tightly interconnected subdomains with strong
clustering coefficients, indicating both diversity and thematic
VOLUME 13, 2025 215027

--- page 26 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
FIGURE 17. Examples of other subgraphs in the interdisciplinary knowledge graph.
concentration. Temporal topic evolution networks from
LDA illustrate a consistent deepening in AI-rehabilitation
integration from 2018 to 2025. The field has evolved from
foundational work on algorithm optimization and assisted
diagnosis to address more complex challenges. Current
research emphasizes multi-technology synergy, ethical con￾siderations, and practical deployment. Furthermore, recent
trends show a clear focus on personalized and community￾oriented applications.
The LLM-KG-LDACX model leverages prompt engineer￾ing with large language models for information extraction,
and we enhance this process through LDA-based entity
verification and complex network matrices. External valida￾tion on PubMed data confirms that its extraction capability
significantly surpasses the BiLSTM-CRF baseline and a
standalone LLM, showing greater potential than a pre-trained
BERT model reliant on annotated data. The resulting knowl￾edge graph, centered on ‘‘artificial intelligence,’’ features a
three-tier structure of ‘‘core technologies,’’ ‘‘application sup￾port,’’ and ‘‘industry applications.’’ Multiple self-contained
subgraphs further map out how specific AI technologies are
applied across diverse rehabilitation scenarios.
B. RESEARCH LIMITATIONS AND EXPANSIONS
This study developed the LLM-KG-LDACX model and
the RehabKD framework to explore AI-driven knowledge
discovery in rehabilitation science through text mining.
Despite its contributions, several limitations require acknowl￾edgment: (1) Limited Data Sources and Practical Scenarios:
Our analysis relied solely on 699 publications from the
Web of Science. The lack of experimental and clinical data
creates a gap between the knowledge graph and real-world
applications, constraining its translational potential. (2) Lack
of Multimodal and Dynamic Information: The framework
uses only text data, omitting multimodal information like
MRI and gait videos. The static knowledge graph cannot
215028 VOLUME 13, 2025

--- page 27 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
capture temporal dynamics, limiting its ability to reflect
real-time knowledge evolution. (3) Insufficient Reasoning
Depth and Decision Support: The LDA model identifies
thematic correlations but lacks causal inference. It cannot
determine if ‘‘machine learning’’ genuinely causes improved
‘‘rehabilitation efficiency.’’ The absence of an intelligent
decision support system reduces practical impact.
Future research should pursue the following directions:
(1) Developing a Dynamic and Multimodal Framework:
Integrating temporal graph neural networks and vision trans￾formers would enable real-time, dynamic knowledge graphs.
Incorporating multimodal data using cross-modal LLMs
would create a richer and more comprehensive knowledge
representation. (2) Enhancing Scientific Decision-Making:
Embedding causal inference modules into topic models
could disentangle causation from correlation. An intelligent
decision support system based on the knowledge graph
could suggest promising or novel research directions. (3)
Fostering Interdisciplinary Collaboration: Expanding the
knowledge graph to integrate multiple disciplines (e.g.,
medicine and engineering) would break down academic silos.
An AI-powered knowledge-sharing platform with interactive
visualization and smart recommendations could accelerate
interdisciplinary innovation.
V. CONCLUSION
This study developed the LLM-KG-LDACX joint model for
information extraction. Using this model, we constructed the
RehabKD knowledge discovery framework, which integrates
large language models, text mining, and knowledge graphs.
Through a systematic analysis of interdisciplinary literature
from the Web of Science, this study uncovers the underlying
knowledge discovery mechanisms in rehabilitation science
and AI. Our work provides a novel paradigm for AI-driven
research in specialized domains. Our key findings are: (1)
Publications in this domain have grown exponentially since
2018, with AI as a core developmental driver. (2) Sentiment
analysis reflects an objective and rational research attitude.
(3) Keyword analysis identifies ‘‘artificial intelligence’’ and
‘‘machine learning’’ as central themes. (4) Clustering explo￾rations using multiple dimensionality reduction algorithms
effectively mapped the semantic space, identifying distinct
research communities. (5) Keyword co-occurrence and com￾plex network analysis reveal tightly knit yet diverse research
subdomains. (6) LDA topic evolution illustrates a consistent
deepening of AI integration in rehabilitation research. (7) We
externally validated the information extraction capability of
our LLM-KG-LDACX model. The results demonstrate that
it significantly outperforms the BiLSTM-CRF baseline and
shows greater potential than a pre-trained BERT model reliant
on annotated data.
Overall, this work provides a reusable ‘‘data mining
– model construction – clinical mapping’’ framework for
rehabilitation science. By integrating multiple AI models,
we validate the potential of data-intensive approaches to drive
knowledge discovery. Thus, our framework demonstrates a
path to advance AI from an auxiliary tool to a genuine
’scientific discovery collaborator.’ This work promotes the
deeper implementation of ’AI for Science’ in specialized
domains like rehabilitation.
ACKNOWLEDGMENT
(Wei Zhang and Zhizhong Xing are co-first authors.)
REFERENCES
[1] R. Yang, Q. Yuan, W. Zhang, H. Cai, and Y. Wu, ‘‘Application of artificial
intelligence in rehabilitation science: A scientometric investigation utiliz￾ing citespace,’’ SLAS Technol., vol. 29, no. 4, Aug. 2024, Art. no. 100162.
[2] F. Lanotte, M. K. O’Brien, and A. Jayaraman, ‘‘AI in rehabilitation
medicine: Opportunities and challenges,’’ Ann. Rehabil. Med., vol. 47,
no. 6, pp. 444–458, Dec. 2023.
[3] P. Philipp, N. Merkle, K. Gand, and C. Gißke, ‘‘Continuous support for
rehabilitation using machine learning,’’ it - Inf. Technol., vol. 61, nos. 5–6,
pp. 273–284, Oct. 2019.
[4] C. Mennella, U. Maniscalco, G. De Pietro, and M. Esposito, ‘‘The role
of artificial intelligence in future rehabilitation services: A systematic
literature review,’’ IEEE Access, vol. 11, pp. 11024–11043, 2023.
[5] Q. Chen et al., ‘‘Benchmarking large language models for biomedical
natural language processing applications and recommendations,’’ Nature
Commun., vol. 16, no. 1, pp. 1–16, Apr. 2025.
[6] Y. Zhang, X. Sui, F. Pan, K. Yu, K. Li, S. Tian, A. Erdengasileng, Q. Han,
W. Wang, J. Wang, J. Wang, D. Sun, H. Chung, J. Zhou, E. Zhou, B.
Lee, P. Zhang, X. Qiu, T. Zhao, and J. Zhang, ‘‘A comprehensive large￾scale biomedical knowledge graph for AI-powered data-driven biomedical
research,’’ Nature Mach. Intell., vol. 7, no. 4, pp. 1–13, Mar. 2025.
[7] X. Wu, J. Duan, Y. Pan, and M. Li, ‘‘Medical knowledge graph: Data
sources, construction, reasoning, and applications,’’ Big Data Mining
Anal., vol. 6, no. 2, pp. 201–217, Jun. 2023.
[8] H. Wang et al., ‘‘Scientific discovery in the age of artificial intelligence,’’
Nature, vol. 620, no. 7972, pp. 47–60, 2023.
[9] S. Musslick, L. K. Bartlett, S. H. Chandramouli, M. Dubova, F. Gobet,
T. L. Griffiths, J. Hullman, R. D. King, J. N. Kutz, C. G. Lucas, S. Mahesh,
F. Pestilli, S. J. Sloman, and W. R. Holmes, ‘‘Automating the practice of
science: Opportunities, challenges, and implications,’’ Proc. Nat. Acad.
Sci. USA, vol. 122, no. 5, Feb. 2025, Art. no. e2401238121.
[10] A. Angelopoulos, J. F. Cahoon, and R. Alterovitz, ‘‘Transforming science
labs into automated factories of discovery,’’ Sci. Robot., vol. 9, no. 95,
Oct. 2024, Art. no. eadm6991.
[11] J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, ‘‘BERT: Pre-training
of deep bidirectional transformers for language understanding,’’ 2018,
arXiv:1810.04805.
[12] M. E. Peters, M. Neumann, R. L. Logan, R. Schwartz, V. Joshi, S. Singh,
and N. A. Smith, ‘‘Knowledge enhanced contextual word representations,’’
2019, arXiv:1909.04164.
[13] X. Liu, J. Wang, J. Sun, X. Yuan, G. Dong, P. Di, W. Wang, and D. Wang,
‘‘Prompting frameworks for large language models: A survey,’’ 2023,
arXiv:2311.12785.
[14] T. Dinh, W. Hauchi, D. Lisik, M. Koren, D. Tran, P. S. Yu, and J. Torres￾Sospedra, ‘‘Data clustering: A fundamental method in data science and
management,’’ 2024, arXiv:2412.18760.
[15] C. C. Aggarwal and C. X. Zhai, ‘‘A survey of text clustering algorithms,’’
in Mining Text Data. Boston, MA, USA: Springer, 2012, pp. 77–128.
[16] G. Liu, L. Xie, and C.-H. Chen, ‘‘Unsupervised text feature learning
via deep variational auto-encoder,’’ Inf. Technol. Control, vol. 49, no. 3,
pp. 421–437, Sep. 2020.
[17] N. Liu, B. Zhang, J. Yan, Z. Chen, W. Liu, F. Bai, and L. Chien, ‘‘Text
representation: From vector to tensor,’’ in Proc. 5th IEEE Int. Conf. Data
Mining, Nov. 2005, pp. 725–728.
[18] H. Heuer, ‘‘Text comparison using word vector representations and
dimensionality reduction,’’ 2016, arXiv:1607.00534.
[19] J. Situ, ‘‘Contrastive learning dimensionality reduction method based on
manifold learning,’’ Adv. Eng. Technol. Res., vol. 9, no. 1, p. 522, Jan. 2024.
[20] Y. Lin and Y. Zhou, ‘‘Identification of hydrogen-energy-related emerging
technologies based on text mining,’’ Sustainability, vol. 16, no. 1, p. 147,
Dec. 2023.
VOLUME 13, 2025 215029

--- page 28 ---
W. Zhang et al.: RehabKD With LLM-KG-LDACX: Orchestrating AI Models for RehabKD
[21] B. Ampel, C.-H. Yang, J. Hu, and H. Chen, ‘‘Large language models for
conducting advanced text analytics information systems research,’’ ACM
Trans. Manage. Inf. Syst., vol. 16, no. 1, pp. 1–27, Mar. 2025.
[22] B. Davazdahemami, H. Zolbanin, and A. Zadeh, ‘‘Revitalizing the
scholarly compass: Harnessing GPT-powered automation for dynamic
aims & scope evolution in academic journals,’’ Commun. Assoc. Inf. Syst.,
vol. 55, no. 1, pp. 1029–1068, 2025.
[23] K. Soman, P. W. Rose, J. H. Morris, R. E. Akbas, B. Smith, B.
Peetoom, C. Villouta-Reyes, G. Cerono, Y. Shi, A. Rizk-Jackson, S. Israni,
C. A. Nelson, S. Huang, and S. E. Baranzini, ‘‘Biomedical knowledge
graph-optimized prompt generation for large language models,’’ Bioinfor￾matics, vol. 40, no. 9, pp. 1–10, Sep. 2024.
[24] M. Dreger, K. Malek, and M. Eikerling, ‘‘Large language models for
knowledge graph extraction from tables in materials science,’’ Digit.
Discovery, vol. 4, no. 5, pp. 1221–1231, May 2025.
[25] J. Dagdelen, A. Dunn, S. Lee, N. Walker, A. S. Rosen, G. Ceder, K. A.
Persson, and A. Jain, ‘‘Structured information extraction from scientific
text with large language models,’’ Nature Commun., vol. 15, no. 1,
pp. 1–14, Feb. 2024.
[26] S. Pan, L. Luo, Y. Wang, C. Chen, J. Wang, and X. Wu, ‘‘Unifying large
language models and knowledge graphs: A roadmap,’’ IEEE Trans. Knowl.
Data Eng., vol. 36, no. 7, pp. 3580–3599, Jul. 2024.
[27] B. Mo, K. Yu, J. Kazdan, J. Cabezas, P. Mpala, L. Yu, C. Cundy,
C. Kanatsoulis, and S. Koyejo, ‘‘KGGen: Extracting knowledge graphs
from plain text with language models,’’ 2025, arXiv:2502.09956.
[28] J. Z. Pan, S. Razniewski, J.-C. Kalo, S. Singhania, J. Chen, S. Dietze,
H. Jabeen, J. Omeliyanenko, W. Zhang, M. Lissandrini, R. Biswas,
G. de Melo, A. Bonifati, E. Vakaj, M. Dragoni, and D. Graux, ‘‘Large
language models and knowledge graphs: Opportunities and challenges,’’
2023, arXiv:2308.06374.
[29] V. Desai, Y. Chi, J. Stephens, and A. Gupta, ‘‘Building model-driven
knowledge graphs via large language models,’’ in Proc. Eur. Conf.
Adv. Databases Inf. Syst. Cham, Switzerland: Springer, Aug. 2024,
pp. 160–172.
[30] A. Kau, X. He, A. Nambissan, A. Astudillo, H. Yin, and A. Aryani,
‘‘Combining knowledge graphs and large language models,’’ 2024,
arXiv:2407.06564.
[31] H. Chaoguang, H. Yueji, H. Fanfan, and Z. Chenwei, ‘‘An approach for
interdisciplinary knowledge discovery: Link prediction between topics,’’
Phys. A, Stat. Mech. Appl., vol. 665, May 2025, Art. no. 130517.
[32] H. Zong, R. Wu, J. Cha, W. Feng, E. Wu, J. Li, A. Shao, L. Tao,
Z. Li, B. Tang, and B. Shen, ‘‘Advancing Chinese biomedical text mining
with community challenges,’’ J. Biomed. Informat., vol. 157, Sep. 2024,
Art. no. 104716.
[33] M. Nickel, K. Murphy, V. Tresp, and E. Gabrilovich, ‘‘A review of
relational machine learning for knowledge graphs,’’ Proc. IEEE, vol. 104,
no. 1, pp. 11–33, Jan. 2016.
[34] J. Boyko, J. Cohen, N. Fox, M. H. Veiga, J. I.-H. Li, J. Liu, B. Modenesi,
A. H. Rauch, K. N. Reid, S. Tribedi, A. Visheratina, and X. Xie, ‘‘An
interdisciplinary outlook on large language models for scientific research,’’
2023, arXiv:2311.04929.
[35] R. Jeyaram, R. N. Ward, and M. Santolini, ‘‘Reconstructing networks
from text using large language models (LLMs),’’ in Proc. 12th Int. Conf.
Complex Netw. Appl., Nov. 2023, pp. 1–5.
[36] V. D. Blondel, J.-L. Guillaume, R. Lambiotte, and E. Lefebvre, ‘‘Fast
unfolding of communities in large networks,’’ J. Stat. Mechanics: Theory
Exp., vol. 2008, no. 10, Oct. 2008, Art. no. P10008.
[37] Q. Zhang, Z. Chen, H. Pan, C. Caragea, L. Jan Latecki, and E. Dragut,
‘‘SciER: An entity and relation extraction dataset for datasets, methods,
and tasks in scientific documents,’’ 2024, arXiv:2410.21155.
WEI ZHANG received the M.S. degree. He is
currently a Lecturer with Kunming Medical Uni￾versity. His research interests include intelligence
science, complex systems, and data mining.
ZHIZHONG XING received the Ph.D. degree.
He is a high-level talent introduced by Kunming
Medical University. He has been working at
Kunming Medical University, since 2023. His
research interests include artificial intelligence,
graph neural networks, and deep learning. He is a
reviewer of many journals, such as IEEE/ASME
TRANSACTIONS ON MECHATRONICS, IEEE SENSORS
JOURNAL, Expert Systems With Applications, Engi￾neering Applications of Artificial Intelligence,
Knowledge-Based Systems, and IEEE TRANSACTIONS ON CYBERNETICS.
SHAOCHUN CHEN received the Ph.D. degree.
He is currently a Professor and the Dean of
the Rehabilitation College, Kunming Medical
University. His research interests include human
anatomy and intelligent rehabilitation.
215030 VOLUME 13, 2025

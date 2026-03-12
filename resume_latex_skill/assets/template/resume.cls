\RequirePackage{expl3,l3keys2e}
\ProvidesExplClass{resume}
{2022-12-26}{0.1.0}{Another Resume Class by Feng Kaiyu}

% Base class setup
\PassOptionsToPackage{quiet}{xeCJK}
\ProcessOptions\relax
\LoadClass[zihao=5,autoindent=0em,fontset=fandol]{ctexart}

\RequirePackage{geometry}
\RequirePackage{fancyhdr}
\RequirePackage{enumitem}
\RequirePackage[para]{footmisc}
\RequirePackage[colorlinks=false,hidelinks]{hyperref}
\RequirePackage{xeCJKfntef}
\RequirePackage{xcolor}
\RequirePackage{fontspec}

\pagestyle{empty}

% Page margins
\geometry{
  a4paper,
  left=1.00cm,
  right=1.00cm,
  top=0.66cm,
  bottom=0.66cm
}

%%% Global Variables %%%
\seq_new:N \g__resume_contacts_seq
\tl_new:N \g__resume_title_name_tl
\seq_new:N \l__resume_contacts_input_seq

%%% Global Settings %%%

\pagenumbering{gobble}

\defaultfontfeatures{Ligatures=TeX}

\definecolor{ResumeText}{HTML}{111111}
\definecolor{ResumeBody}{HTML}{242424}
\definecolor{ResumeMuted}{HTML}{3E434A}
\definecolor{ResumeRule}{HTML}{111111}
\definecolor{ResumeLink}{HTML}{2A2F36}

\setmainfont[
  Scale=MatchUppercase,
  Numbers={Lining,Proportional}
]{Arial}

\setsansfont[
  Scale=MatchUppercase,
  Numbers={Lining,Proportional}
]{Arial}

\setCJKmainfont[
  Path=./fonts/,
  UprightFont = NotoSansSC-Regular.ttf,
  BoldFont = NotoSansSC-Bold.ttf,
  FontFace = {sb}{n}{NotoSansSC-SemiBold.ttf},
  FontFace = {eb}{n}{NotoSansSC-ExtraBold.ttf}
]{NotoSansSC}

\setCJKsansfont[
  Path=./fonts/,
  UprightFont = NotoSansSC-Regular.ttf,
  BoldFont = NotoSansSC-Bold.ttf,
  FontFace = {sb}{n}{NotoSansSC-SemiBold.ttf},
  FontFace = {eb}{n}{NotoSansSC-ExtraBold.ttf}
]{NotoSansSC}

\NewDocumentCommand{\CJKSemiBold}{}{\fontseries{sb}\selectfont}
\NewDocumentCommand{\CJKBold}{}{\bfseries}
\NewDocumentCommand{\CJKExtraBold}{}{\fontseries{eb}\selectfont}

\xeCJKsetup{
  CJKglue = \hskip 0pt plus 0.05\baselineskip,
  PunctStyle = kaiming,
  CheckSingle = true
}

\renewcommand{\familydefault}{\sfdefault}
\color{ResumeBody}

\linespread{1.10}

\ctexset{
  section = {
    nameformat = {},
    number = {},
    format = \noindent \zihao{-4} \CJKExtraBold \__resume_section_title_format:n,
    indent = -1em,
    afterskip = 0.68em,
    beforeskip = 0.56em,
  },
}

% Default list rhythm
\setlist{
  labelsep=3pt,
  labelwidth=5pt,
  leftmargin=1.24em,
  itemsep=0.10em,
  parsep=0em,
  topsep=0.28em,
  partopsep=0em,
}

\setlist[itemize,1]{label=\textbullet,leftmargin=1.24em}
\setlist[itemize,2]{label=\raisebox{0.18ex}{\scriptsize$\circ$},leftmargin=1.95em,itemsep=0.04em,topsep=0.06em}
\setlist[itemize,3]{label=\raisebox{0.18ex}{\tiny$\diamond$},leftmargin=2.55em,itemsep=0.02em,topsep=0.04em}
\setlist[itemize,4]{label=\textendash,leftmargin=3.05em,itemsep=0.01em,topsep=0.03em}

\newcounter{resumebookmark}

%%% User Commands %%%

\cs_new:Npn \__resume_append_concat:n #1
{
  \seq_put_right:Nn \g__resume_contacts_seq {#1}
}

\cs_new:Npn \__resume_section_title_format:n #1
{{\color{ResumeText}#1} \par \vspace{3pt} {\color{ResumeRule}\hrule height 0.8pt}}

\NewDocumentCommand{\ResumeContact}{m}
{
  \__resume_append_concat:n {#1}
}

\NewDocumentCommand{\ResumeContacts}{m}
{
  \seq_set_from_clist:Nn \l__resume_contacts_input_seq {#1}
  \seq_map_inline:Nn \l__resume_contacts_input_seq
  {
    \__resume_append_concat:n {##1}
  }
}

\NewDocumentCommand{\ResumeName}{m}
{
  \tl_set:Nn \g__resume_title_name_tl {#1}
}

\NewDocumentCommand{\ResumeTitle}{}
{
  \begin{center}
    {\color{ResumeText}\zihao{2} \sffamily \CJKExtraBold \g__resume_title_name_tl}
  \end{center}
  \vspace{-0.7em}
  \begin{center}
    {\small\color{ResumeMuted}
    \seq_use:Nnnn \g__resume_contacts_seq {~|~} {~|~} {~|~}
    }
  \end{center}
  \vspace{0.08em}
}

\NewDocumentCommand{\ResumeItem}{omoo}
{
  {
    \zihao{5}
    \par
    \noindent
    {
      \color{ResumeText}\CJKSemiBold
      #2

      \IfValueTF{#1}
      {
        \pdfbookmark[2]{#1}{subsec:\arabic{resumebookmark}}
      }
      {
        \pdfbookmark[2]{#2}{subsec:\arabic{resumebookmark}}
      }
      \stepcounter{resumebookmark}
    }
    \IfValueT{#3}{
      \tl_if_empty:nF {#3} {
        {\color{ResumeMuted}\bfseries\ | #3}
      }
    }
    \hfill
    \IfValueT{#4}{{\color{ResumeMuted}\bfseries #4}}
    \par\vspace{0.28em}
  }
}

\NewDocumentEnvironment{ResumeCompactList}{}{\begin{itemize}[topsep=0.08em]}{\end{itemize}}

\NewDocumentCommand{\ResumeEduItem}{omoo}
{
  {
    \zihao{5}
    \noindent
    \mbox{%
      {\color{ResumeText}\CJKSemiBold #2}%
      \IfValueT{#3}{\kern0.16em{\color{ResumeMuted}\bfseries|~#3}}%
    }%
    \IfValueTF{#1}
    {
      \pdfbookmark[2]{#1}{subsec:\arabic{resumebookmark}}
    }
    {
      \pdfbookmark[2]{#2}{subsec:\arabic{resumebookmark}}
    }
    \stepcounter{resumebookmark}
    \hfill
    \IfValueT{#4}{{\color{ResumeMuted}\bfseries #4}}
    \par\vspace{0.00em}
  }
}

\NewDocumentCommand{\ResumeHeaderStackGap}{}{\vspace{1pt}}
\NewDocumentCommand{\ResumeHeaderBodyGap}{}{\vspace{0.04cm}}

\NewDocumentCommand{\GrayText}{m}
{
  \textcolor{ResumeMuted}{#1}
}

\NewDocumentCommand{\ResumeUrl}{mm}
{
  {\begingroup
  \color{ResumeText}
  \xeCJKsetup{underline/format=\color{ResumeText}, underline/thickness=0.06em}
  \href{#1}{\CJKunderline{#2}}
  \endgroup}
}

\NewDocumentCommand{\ResumeHeaderName}{m}
{
  {\fontsize{15.2pt}{15.8pt}\selectfont\CJKSemiBold\color{ResumeText}#1}
}

\NewDocumentCommand{\ResumeHeaderMeta}{m}
{
  {\fontsize{8.8pt}{9.4pt}\selectfont\color{ResumeMuted}#1}
}

\NewDocumentCommand{\ResumeHeaderIntent}{m}
{
  {\fontsize{8.8pt}{9.4pt}\selectfont\color{ResumeMuted}#1}
}

\endinput

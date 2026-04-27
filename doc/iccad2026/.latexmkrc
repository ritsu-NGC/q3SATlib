# latexmk configuration for doc/isvlsi2026/main.tex

$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -file-line-error -synctex=1 %O %S';

# Bibliography (project has ref.bib)
$bibtex = 'bibtex %O %B';

# Keep outputs tidy
$aux_dir  = 'build';
$out_dir  = 'build';

@default_files = ('main.tex');

$clean_ext .= ' acn acr alg glg glo gls glsdefs ist loa lof lot lol '
            . ' nav out snm synctex.gz toc xdy run.xml bbl blg';

# --- Fail the build on missing refs/cites ---
# latexmk scans the .log and treats matching patterns as "warnings".
# If a warning is set with severity >= 2, latexmk will return a non-zero exit code.
# (This does not necessarily stop mid-run, but it will fail CI.)
$warnings_as_errors = 1;

# Undefined references and citations:
#   LaTeX Warning: Reference `...' on page ... undefined
#   LaTeX Warning: Citation `...' on page ... undefined
# Also catch natbib variants (if used).
$warning_list{ 'undefined_refs' } = {
  'regex' => qr/LaTeX Warning: Reference `[^']+' on page \d+ undefined/,
  'msg'   => 'Undefined reference(s)',
  'level' => 2,
};
$warning_list{ 'undefined_cites' } = {
  'regex' => qr/LaTeX Warning: Citation `[^']+' on page \d+ undefined/,
  'msg'   => 'Undefined citation(s)',
  'level' => 2,
};
$warning_list{ 'natbib_undefined_cites' } = {
  'regex' => qr/Package natbib Warning: Citation `[^']+' on page \d+ undefined/,
  'msg'   => 'Undefined citation(s) (natbib)',
  'level' => 2,
};

# Closely related: label(s) may have changed (often indicates unresolved refs until rerun)
$warning_list{ 'label_changed' } = {
  'regex' => qr/LaTeX Warning: Label\(s\) may have changed\. Rerun to get cross-references right\./,
  'msg'   => 'Labels changed (needs rerun)',
  'level' => 2,
};

# Common “??” symptom in log:
$warning_list{ 'rerun_needed' } = {
  'regex' => qr/LaTeX Warning: There were undefined references\./,
  'msg'   => 'There were undefined references',
  'level' => 2,
}; 
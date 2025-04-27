import pypandoc

pypandoc.convert_file(
    'paper.md', 'pdf',
    outputfile='README.pdf',
    extra_args=['--highlight-style', 'tango']
)
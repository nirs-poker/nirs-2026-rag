param([Parameter(Mandatory)][string] $TheoryDirectory)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$word = New-Object -ComObject Word.Application
$doNotSave = 0
try {
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $files = [ordered]@{}
    foreach ($file in Get-ChildItem -LiteralPath $TheoryDirectory -Filter '*.doc' -File) {
        $doc = $word.Documents.Open($file.FullName, $false, $true, $false)
        try {
            $files[$file.Name] = @(
                foreach ($paragraph in $doc.Paragraphs) {
                    $text = $paragraph.Range.Text.Trim() -replace '[\r\v]', "`n"
                    if ($text) {
                        @{ text = $text; heading = ($paragraph.Range.Font.Bold -eq -1) }
                    }
                }
            )
        } finally {
            $doc.Close([ref]$doNotSave)
        }
    }
    ConvertTo-Json -InputObject $files -Depth 6 -Compress
} finally {
    $word.Quit([ref]$doNotSave)
}

$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $item = Get-ChildItem -Path "docs" -Filter "*SOA.docx" | Where-Object { $_.Name -notlike "*backup*" -and $_.Name -notlike "*temp*" } | Select-Object -First 1
    $docPath = $item.FullName
    $pdfPath = [System.IO.Path]::ChangeExtension($docPath, ".pdf")
    Write-Host "Opening $docPath..."
    $doc = $word.Documents.Open($docPath)
    Write-Host "Exporting to $pdfPath..."
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    $doc.Close([ref]0)
    Write-Host "Exported PDF successfully: $pdfPath"
} finally {
    $word.Quit()
}

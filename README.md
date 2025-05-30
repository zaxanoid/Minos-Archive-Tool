G8ZAX Minos Archive tool. 
Allows multiple .cls, .edi and .minos files for be combined into an archive file


I wrote this because I could not find anything which did exactly what I wanted.

My requirements:
1) To be able to import a bunch of files in one go
2) For any comments in the .Minos files, to be put in the correct place in the archive file, such that these can be seen when a match is found
3) De-duplication of identical callsign/locator
4) Output file sorted by callsign, easier to find an entry for manual correction if needed

It appears to work, and I have used it to create an archive file from over 100 Minos database files in one go. 
Solved my problem, but ....
It is badly written, has very few comments and is "as is". I am not a python programmer, but I am learning. 
I am releasing this here in case it is of use to you. 

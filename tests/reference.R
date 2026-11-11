library(SingleCellExperiment)
library(nnls)
ref <- commandArgs(TRUE)[1]
for (f in c('analysis.R','construct.R','utils.R')) source(file.path(ref,'R',f))
set.seed(42)
ct <- rep(rep(c('A','B','C'),each=10),4)
donor <- rep(paste0('d',1:4),each=30)
counts <- matrix(rpois(100*120,5),100,120)
for (j in 1:3) counts[((j-1)*25+1):(j*25),ct==c('A','B','C')[j]] <-
    counts[((j-1)*25+1):(j*25),ct==c('A','B','C')[j]]+12
rownames(counts)<-paste0('g',1:100);colnames(counts)<-paste0('c',1:120)
sce <- SingleCellExperiment(list(counts=counts),colData=data.frame(ct=ct,donor=donor))
basis<-music_basis(sce,clusters='ct',samples='donor',verbose=FALSE)
mixture<-matrix(c(.2,.3,.5,.6,.2,.2,.3,.5,.2),3,3)
bulk<-basis$Disgn.mtx%*%mixture*100
colnames(bulk)<-paste0('b',1:3)
bulk[1,1]<-0
write.csv(counts,'data/reference.csv');write.csv(bulk,'data/bulk.csv')
write.csv(data.frame(ct=ct,donor=donor,row.names=colnames(counts)),'data/metadata.csv')
write.csv(basis$Disgn.mtx,'data/design.csv');write.csv(basis$Sigma,'data/variance.csv')
write.csv(basis$S,'data/library_size.csv')
for (mode in c('default','markers')) {
    result<-music_prop(bulk,sce,clusters='ct',samples='donor',
                      markers=if(mode=='markers') rownames(counts)[1:80] else NULL,verbose=FALSE)
    for (key in names(result)) write.csv(result[[key]],paste0('data/',mode,'_',key,'.csv'))
}
